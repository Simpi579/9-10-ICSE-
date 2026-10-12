"""
Repository for retrieving and managing existing questions from the question bank.
Ensures original questions are preserved and never overwritten inadvertently.
"""

import json
import os
from typing import Dict, List, Optional

from schema.enums import QuestionType, RubricVerificationStatus
from schema.models import Question, MCQQuestion, SubjectiveQuestion, RubricCriterion


class QuestionRepository:
    """
    Manages access to the existing CBSE question bank.
    """

    def __init__(self, data_file_path: Optional[str] = None):
        if data_file_path:
            self.file_path = os.path.abspath(data_file_path)
        else:
            # Default to data/cbse_class9_history_questions.json relative to project root
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.file_path = os.path.join(base_dir, "data", "cbse_class9_history_questions.json")

        self._questions: Dict[str, Question] = {}
        self.load()

    def load(self) -> None:
        """
        Loads questions from the persistent JSON store into typed Pydantic models.
        """
        if not os.path.exists(self.file_path):
            self._questions = {}
            return

        with open(self.file_path, "r", encoding="utf-8") as f:
            raw_list = json.load(f)

        self._questions = {}
        for item in raw_list:
            q_id = item.get("question_id")
            q_type = item.get("question_type")
            try:
                if q_type == "MCQ" or q_type == QuestionType.MCQ:
                    question = MCQQuestion(**item)
                else:
                    question = SubjectiveQuestion(**item)
                self._questions[q_id] = question
            except Exception as e:
                # Log or handle corrupted records gracefully
                continue

    def get_question(self, question_id: str) -> Optional[Question]:
        """
        Retrieves a question by its unique identifier.
        """
        return self._questions.get(question_id)

    def list_all_questions(self) -> List[Question]:
        """
        Returns all questions currently in the repository.
        """
        return list(self._questions.values())

    def list_questions_by_chapter(self, chapter: str) -> List[Question]:
        """
        Filters questions by chapter name.
        """
        norm_chapter = chapter.strip().lower()
        return [
            q for q in self._questions.values()
            if q.chapter.strip().lower() == norm_chapter
        ]

    def list_chapters(self) -> List[str]:
        """
        Returns a sorted list of unique chapters available in the question bank.
        """
        chapters = {q.chapter for q in self._questions.values()}
        return sorted(list(chapters))

    def update_question_rubric(
        self,
        question_id: str,
        rubric: List[RubricCriterion],
        expected_answer: str,
        verified: bool = False,
    ) -> bool:
        """
        Allows authorized updating of a question's marking rubric and model answer.
        """
        question = self.get_question(question_id)
        if not question or not isinstance(question, SubjectiveQuestion):
            return False

        question.marking_rubric = rubric
        question.expected_answer = expected_answer
        question.rubric_status = (
            RubricVerificationStatus.VERIFIED if verified
            else RubricVerificationStatus.UNVERIFIED
        )

        # Save changes persistently
        return self.save()

    def save(self) -> bool:
        """
        Persists all loaded questions back to the JSON storage file.
        """
        os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
        serialized = [q.model_dump() for q in self._questions.values()]
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(serialized, f, indent=2)
        return True
