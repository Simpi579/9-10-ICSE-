"""
Question Generator orchestrator.
Manages LLM communication, response cleaning, parsing, and pipeline validation.
Enforces programmatic security constraints (source_type override and status assignment).
"""

import json
import logging
import re
from typing import Any, Dict, Optional

from llm_module.client import GeminiClient
from schema.enums import (
    Board,
    ClassGrade,
    Subject,
    QuestionType,
    Difficulty,
    SourceType,
    ValidationStatus,
)
from schema.models import ValidationResult, Question
from validation.pipeline import ValidationPipeline
from .prompts import PromptBuilder

logger = logging.getLogger(__name__)


class QuestionGenerator:
    """
    Coordinates LLM question generation and deterministic validation.
    """

    def __init__(
        self,
        client: Optional[GeminiClient] = None,
        pipeline: Optional[ValidationPipeline] = None,
    ):
        self.client = client
        self.pipeline = pipeline or ValidationPipeline()

    @staticmethod
    def clean_json_response(raw_text: str) -> str:
        """
        Removes markdown wrappers (```json ... ```) or extraneous formatting.
        """
        text = raw_text.strip()
        # Regex to strip ```json ... ``` or ``` ... ```
        match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        if match:
            text = match.group(1).strip()
        return text

    def parse_and_validate(
        self,
        raw_response: str,
        question_type: QuestionType,
        expected_metadata: Optional[Dict[str, Any]] = None,
    ) -> ValidationResult:
        """
        Parses raw text response from LLM, merges canonical metadata,
        and executes the strict validation pipeline.
        Programmatically overrides source_type to LLM_GENERATED.
        """
        cleaned = self.clean_json_response(raw_response)

        # 1. Parse JSON safely
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as err:
            logger.error(f"Failed to parse LLM response as JSON: {err}")
            return ValidationResult(
                is_valid=False,
                status=ValidationStatus.INVALID,
                errors=[f"Malformed JSON from AI model: {str(err)}"],
                warnings=[],
                validated_question=None,
            )

        if not isinstance(data, dict):
            return ValidationResult(
                is_valid=False,
                status=ValidationStatus.INVALID,
                errors=["AI response JSON must be a top-level JSON object/dictionary."],
                warnings=[],
                validated_question=None,
            )

        # 2. Merge and enforce canonical metadata
        meta = expected_metadata or {}
        data["question_type"] = question_type.value
        if "board" in meta:
            data["board"] = meta["board"].value if isinstance(meta["board"], Board) else meta["board"]
        if "class_grade" in meta:
            data["class_grade"] = meta["class_grade"].value if isinstance(meta["class_grade"], ClassGrade) else meta["class_grade"]
        if "subject" in meta:
            data["subject"] = meta["subject"].value if isinstance(meta["subject"], Subject) else meta["subject"]
        if "chapter" in meta and meta["chapter"]:
            data["chapter"] = meta["chapter"]
        if "topic" in meta and meta["topic"]:
            data["topic"] = meta["topic"]
        if "difficulty" in meta:
            data["difficulty"] = meta["difficulty"].value if isinstance(meta["difficulty"], Difficulty) else meta["difficulty"]
        if "maximum_marks" in meta:
            data["maximum_marks"] = meta["maximum_marks"]

        # Ensure question_id is set if not provided
        if "question_id" not in data or not data["question_id"]:
            from uuid import uuid4
            data["question_id"] = f"gen_{uuid4().hex[:8]}"

        # 3. Pass through decoupled validation pipeline
        # Note: pipeline.process programmatically sets source_type = LLM_GENERATED
        # and determines validation_status programmatically.
        result = self.pipeline.process(
            raw_data=data,
            question_type=question_type,
            force_source_type=SourceType.LLM_GENERATED,
        )

        return result

    def generate(
        self,
        board: Board = Board.CBSE,
        class_grade: ClassGrade = ClassGrade.CLASS_9,
        subject: Subject = Subject.HISTORY,
        chapter: str = "The French Revolution",
        topic: Optional[str] = None,
        question_type: QuestionType = QuestionType.SHORT_ANSWER,
        difficulty: Difficulty = Difficulty.MEDIUM,
        maximum_marks: float = 3.0,
    ) -> ValidationResult:
        """
        Prompts Gemini to generate a question, cleans the output, and validates it.
        """
        if self.client is None:
            raise RuntimeError("GeminiClient is not initialized. Please configure an API key or provide a mock client.")

        if question_type == QuestionType.MCQ:
            prompt = PromptBuilder.build_mcq_prompt(
                board=board,
                class_grade=class_grade,
                subject=subject,
                chapter=chapter,
                topic=topic,
                difficulty=difficulty,
            )
        else:
            prompt = PromptBuilder.build_subjective_prompt(
                board=board,
                class_grade=class_grade,
                subject=subject,
                chapter=chapter,
                topic=topic,
                question_type=question_type,
                difficulty=difficulty,
                maximum_marks=maximum_marks,
            )

        logger.info(f"Generating {question_type.value} question for {board.value} {class_grade.value} {subject.value} - {chapter}...")
        raw_response = self.client.generate_json(
            prompt=prompt,
            system_instruction=PromptBuilder.SYSTEM_INSTRUCTION,
        )

        expected_meta = {
            "board": board,
            "class_grade": class_grade,
            "subject": subject,
            "chapter": chapter,
            "topic": topic,
            "difficulty": difficulty,
            "maximum_marks": 1.0 if question_type == QuestionType.MCQ else maximum_marks,
        }

        return self.parse_and_validate(
            raw_response=raw_response,
            question_type=question_type,
            expected_metadata=expected_meta,
        )
