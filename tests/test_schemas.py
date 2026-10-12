"""
Unit tests for Pydantic schema validation.
"""

import unittest
from pydantic import ValidationError

from schema.enums import (
    Board,
    ClassGrade,
    Subject,
    QuestionType,
    Difficulty,
    SourceType,
    ValidationStatus,
    RubricVerificationStatus,
)
from schema.models import (
    MCQQuestion,
    SubjectiveQuestion,
    RubricCriterion,
)


class TestQuestionSchemas(unittest.TestCase):

    def test_valid_mcq_creation(self):
        mcq = MCQQuestion(
            question_text="Who was the King of France during the Revolution of 1789?",
            options=["Louis XIV", "Louis XV", "Louis XVI", "Louis XVIII"],
            correct_answer="Louis XVI",
            explanation="Louis XVI ascended the throne of France in 1774 and was king in 1789.",
            chapter="The French Revolution",
            maximum_marks=1.0,
        )
        self.assertEqual(mcq.question_type, QuestionType.MCQ)
        self.assertEqual(mcq.maximum_marks, 1.0)
        self.assertEqual(len(mcq.options), 4)
        self.assertEqual(mcq.correct_answer, "Louis XVI")
        self.assertEqual(mcq.source_type, SourceType.LLM_GENERATED)

    def test_mcq_rejects_fewer_than_four_options(self):
        with self.assertRaises(ValidationError) as ctx:
            MCQQuestion(
                question_text="Who was the King of France?",
                options=["Louis XIV", "Louis XV", "Louis XVI"],  # Only 3 options
                correct_answer="Louis XVI",
                explanation="Valid explanation",
                chapter="The French Revolution",
            )
        self.assertIn("exactly 4 options", str(ctx.exception))

    def test_mcq_rejects_more_than_four_options(self):
        with self.assertRaises(ValidationError) as ctx:
            MCQQuestion(
                question_text="Who was the King of France?",
                options=["Louis XIV", "Louis XV", "Louis XVI", "Louis XVII", "Louis XVIII"],
                correct_answer="Louis XVI",
                explanation="Valid explanation",
                chapter="The French Revolution",
            )
        self.assertIn("exactly 4 options", str(ctx.exception))

    def test_mcq_rejects_duplicate_options(self):
        with self.assertRaises(ValidationError) as ctx:
            MCQQuestion(
                question_text="Who was the King of France?",
                options=["Louis XVI", "Louis XV", "louis xvi", "Louis XIV"],  # Duplicate case-insensitively
                correct_answer="Louis XVI",
                explanation="Valid explanation",
                chapter="The French Revolution",
            )
        self.assertIn("unique", str(ctx.exception).lower())

    def test_mcq_rejects_mismatched_correct_answer(self):
        with self.assertRaises(ValidationError) as ctx:
            MCQQuestion(
                question_text="Who was the King of France?",
                options=["Louis XIV", "Louis XV", "Louis XVI", "Louis XVIII"],
                correct_answer="Napoleon Bonaparte",  # Not in options
                explanation="Valid explanation",
                chapter="The French Revolution",
            )
        self.assertIn("does not match any of the provided options", str(ctx.exception))

    def test_valid_subjective_question_creation(self):
        rubric = [
            RubricCriterion(
                point="Mentioning the financial crisis and empty royal treasury under Louis XVI",
                allocated_marks=1.0,
            ),
            RubricCriterion(
                point="Mentioning the subsistence crisis and rising price of bread",
                allocated_marks=1.0,
            ),
            RubricCriterion(
                point="Describing the unfair taxation borne solely by the Third Estate",
                allocated_marks=1.0,
            ),
        ]
        q = SubjectiveQuestion(
            question_text="Explain the economic causes of the French Revolution.",
            question_type=QuestionType.SHORT_ANSWER,
            expected_answer="The economic causes included empty royal treasury, subsistence crisis, and unequal taxes.",
            marking_rubric=rubric,
            maximum_marks=3.0,
            chapter="The French Revolution",
        )
        self.assertEqual(q.question_type, QuestionType.SHORT_ANSWER)
        self.assertEqual(q.maximum_marks, 3.0)
        self.assertEqual(len(q.marking_rubric), 3)

    def test_subjective_rejects_rubric_sum_mismatch(self):
        rubric = [
            RubricCriterion(point="Point 1", allocated_marks=1.0),
            RubricCriterion(point="Point 2", allocated_marks=1.0),
        ]
        # Total rubric marks = 2.0, but maximum_marks = 3.0
        with self.assertRaises(ValidationError) as ctx:
            SubjectiveQuestion(
                question_text="Explain the causes of the French Revolution.",
                question_type=QuestionType.SHORT_ANSWER,
                expected_answer="Economic, social and political causes.",
                marking_rubric=rubric,
                maximum_marks=3.0,
                chapter="The French Revolution",
            )
        self.assertIn("does not match maximum_marks", str(ctx.exception))

    def test_subjective_rejects_mcq_question_type(self):
        rubric = [RubricCriterion(point="Point 1", allocated_marks=1.0)]
        with self.assertRaises(ValidationError) as ctx:
            SubjectiveQuestion(
                question_text="Explain the causes of the French Revolution.",
                question_type=QuestionType.MCQ,  # Invalid for SubjectiveQuestion
                expected_answer="Detailed answer here.",
                marking_rubric=rubric,
                maximum_marks=1.0,
                chapter="The French Revolution",
            )
        self.assertIn("cannot be MCQ", str(ctx.exception))

    def test_rejects_negative_or_zero_marks(self):
        with self.assertRaises(ValidationError):
            MCQQuestion(
                question_text="Who was the King of France?",
                options=["A", "B", "C", "D"],
                correct_answer="A",
                explanation="Valid explanation",
                chapter="The French Revolution",
                maximum_marks=0.0,
            )


if __name__ == "__main__":
    unittest.main()
