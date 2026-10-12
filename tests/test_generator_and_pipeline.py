"""
Integration and pipeline tests for QuestionGenerator and ValidationPipeline.
Verifies programmatic source_type and validation_status enforcement and mock LLM generation.
"""

import json
import unittest
from unittest.mock import MagicMock

from schema.enums import (
    Board,
    ClassGrade,
    Subject,
    QuestionType,
    Difficulty,
    SourceType,
    ValidationStatus,
)
from schema.models import MCQQuestion, SubjectiveQuestion
from validation.pipeline import ValidationPipeline
from generation.generator import QuestionGenerator


class TestGeneratorAndPipeline(unittest.TestCase):

    def setUp(self):
        self.pipeline = ValidationPipeline()
        self.generator = QuestionGenerator(pipeline=self.pipeline)

    def test_enforces_source_type_llm_generated(self):
        """
        Verify requirement 1: Enforce source_type = 'LLM_GENERATED' programmatically in Python.
        Even if the raw JSON claims it came from a TEXTBOOK or TEACHER_CREATED, Python must override it.
        """
        raw_payload = {
            "question_text": "On which date did the storming of the Bastille take place?",
            "options": ["14 July 1789", "5 May 1789", "20 June 1789", "4 August 1789"],
            "correct_answer": "14 July 1789",
            "explanation": "The storming of the Bastille occurred on the morning of 14 July 1789.",
            "maximum_marks": 1.0,
            "chapter": "The French Revolution",
            # Untrusted attempts to claim different provenance:
            "source_type": "TEXTBOOK",
            "validation_status": "VALID",
        }

        result = self.generator.parse_and_validate(
            raw_response=json.dumps(raw_payload),
            question_type=QuestionType.MCQ,
            expected_metadata={
                "board": Board.CBSE,
                "class_grade": ClassGrade.CLASS_9,
                "subject": Subject.HISTORY,
                "chapter": "The French Revolution",
            },
        )

        self.assertTrue(result.is_valid)
        self.assertEqual(result.status, ValidationStatus.VALID)
        q = result.validated_question
        self.assertIsNotNone(q)
        # CRITICAL ASSERTION: Must be LLM_GENERATED, not TEXTBOOK!
        self.assertEqual(q.source_type, SourceType.LLM_GENERATED)

    def test_programmatically_sets_validation_status(self):
        """
        Verify requirement 2: validation_status is computed programmatically by deterministic validation.
        """
        # Malformed question with duplicate options
        bad_payload = {
            "question_text": "Who was the ruler of Russia in 1914?",
            "options": ["Tsar Nicholas II", "Lenin", "Tsar Nicholas II", "Stalin"],
            "correct_answer": "Tsar Nicholas II",
            "explanation": "Tsar Nicholas II ruled Russia in 1914.",
            "maximum_marks": 1.0,
            "chapter": "Socialism in Europe and the Russian Revolution",
            "validation_status": "VALID",  # Untrusted LLM claim
        }

        result = self.generator.parse_and_validate(
            raw_response=json.dumps(bad_payload),
            question_type=QuestionType.MCQ,
            expected_metadata={
                "board": Board.CBSE,
                "class_grade": ClassGrade.CLASS_9,
                "subject": Subject.HISTORY,
                "chapter": "Socialism in Europe and the Russian Revolution",
            },
        )

        self.assertFalse(result.is_valid)
        self.assertEqual(result.status, ValidationStatus.INVALID)
        self.assertTrue(any("unique" in err.lower() for err in result.errors))

    def test_handles_malformed_json_gracefully(self):
        """
        Verify requirement 9: Malformed JSON produces a clear error without crashing.
        """
        broken_json = "{'question_text': 'Who was Louis XVI?', options: ['A', 'B'}"  # Invalid JSON syntax
        result = self.generator.parse_and_validate(
            raw_response=broken_json,
            question_type=QuestionType.MCQ,
        )
        self.assertFalse(result.is_valid)
        self.assertEqual(result.status, ValidationStatus.INVALID)
        self.assertTrue(any("Malformed JSON" in err for err in result.errors))

    def test_strips_markdown_code_fences(self):
        """
        Verify generator cleans ```json ... ``` fences produced by LLMs.
        """
        fenced_payload = """```json
        {
            "question_text": "What was the main demand of the women's march to Versailles?",
            "options": ["Bread for their families", "Lower taxes on salt", "Voting rights", "Free land"],
            "correct_answer": "Bread for their families",
            "explanation": "On 5 October 1789, Parisian women marched to Versailles demanding bread.",
            "maximum_marks": 1.0,
            "chapter": "The French Revolution"
        }
        ```"""

        result = self.generator.parse_and_validate(
            raw_response=fenced_payload,
            question_type=QuestionType.MCQ,
            expected_metadata={
                "board": Board.CBSE,
                "class_grade": ClassGrade.CLASS_9,
                "subject": Subject.HISTORY,
                "chapter": "The French Revolution",
            },
        )
        self.assertTrue(result.is_valid)
        self.assertEqual(result.status, ValidationStatus.VALID)

    def test_mock_llm_generation_subjective_history(self):
        """
        End-to-end mock generation test for CBSE Class 9 History Subjective question with rubrics.
        """
        mock_client = MagicMock()
        mock_response_json = json.dumps({
            "question_text": "Examine the role of philosophers in inspiring the French Revolution.",
            "expected_answer": (
                "Philosophers like Montesquieu, Voltaire, and Rousseau played a pivotal role. "
                "Montesquieu proposed division of power between legislature, executive, and judiciary. "
                "Rousseau proposed a social contract government based on democratic ideals. "
                "These ideas were discussed in salons and coffee-houses, mobilizing public opinion against absolute monarchy."
            ),
            "marking_rubric": [
                {
                    "point": "Mentioning Montesquieu and separation of powers (The Spirit of the Laws)",
                    "allocated_marks": 1.0,
                    "description": "Award 1 mark for citing Montesquieu's theory of separation of powers.",
                },
                {
                    "point": "Mentioning Rousseau and government based on a social contract",
                    "allocated_marks": 1.0,
                    "description": "Award 1 mark for mentioning Rousseau's social contract theory.",
                },
                {
                    "point": "Dissemination of ideas through salons, books, and public reading",
                    "allocated_marks": 1.0,
                    "description": "Award 1 mark for explaining how Enlightenment ideas spread among the public.",
                },
            ],
            "difficulty": "Medium",
            "maximum_marks": 3.0,
            "chapter": "The French Revolution",
        })
        mock_client.generate_json.return_value = mock_response_json

        gen = QuestionGenerator(client=mock_client, pipeline=self.pipeline)
        result = gen.generate(
            board=Board.CBSE,
            class_grade=ClassGrade.CLASS_9,
            subject=Subject.HISTORY,
            chapter="The French Revolution",
            question_type=QuestionType.SHORT_ANSWER,
            maximum_marks=3.0,
        )

        self.assertTrue(result.is_valid)
        self.assertEqual(result.status, ValidationStatus.VALID)
        q: SubjectiveQuestion = result.validated_question
        self.assertEqual(q.maximum_marks, 3.0)
        self.assertEqual(len(q.marking_rubric), 3)
        self.assertEqual(q.source_type, SourceType.LLM_GENERATED)


if __name__ == "__main__":
    unittest.main()
