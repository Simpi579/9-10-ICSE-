"""
Unit tests for StructuralValidator.
"""

import unittest
from schema.enums import QuestionType, ValidationStatus
from validation.structural import StructuralValidator


class TestStructuralValidator(unittest.TestCase):

    def setUp(self):
        self.validator = StructuralValidator()

    def test_valid_mcq_data(self):
        data = {
            "question_text": "In which year did the storming of the Bastille occur?",
            "options": ["1789", "1791", "1793", "1799"],
            "correct_answer": "1789",
            "explanation": "The Bastille was stormed on July 14, 1789 in Paris.",
            "chapter": "The French Revolution",
            "maximum_marks": 1.0,
        }
        res = self.validator.validate(data, QuestionType.MCQ)
        self.assertTrue(res.is_valid)
        self.assertEqual(res.status, ValidationStatus.VALID)
        self.assertEqual(len(res.errors), 0)
        self.assertIsNotNone(res.validated_question)

    def test_mcq_missing_fields(self):
        # Missing options and explanation
        data = {
            "question_text": "In which year did the storming of the Bastille occur?",
            "correct_answer": "1789",
        }
        res = self.validator.validate(data, QuestionType.MCQ)
        self.assertFalse(res.is_valid)
        self.assertEqual(res.status, ValidationStatus.INVALID)
        self.assertTrue(any("options" in err.lower() for err in res.errors))

    def test_mcq_duplicate_options(self):
        data = {
            "question_text": "In which year did the storming of the Bastille occur?",
            "options": ["1789", "1791", "1789", "1799"],
            "correct_answer": "1789",
            "explanation": "The Bastille was stormed in 1789.",
            "chapter": "The French Revolution",
            "maximum_marks": 1.0,
        }
        res = self.validator.validate(data, QuestionType.MCQ)
        self.assertFalse(res.is_valid)
        self.assertTrue(any("unique" in err.lower() for err in res.errors))

    def test_mcq_wrong_number_of_options(self):
        data = {
            "question_text": "In which year did the storming of the Bastille occur?",
            "options": ["1789", "1791"],
            "correct_answer": "1789",
            "explanation": "The Bastille was stormed in 1789.",
            "chapter": "The French Revolution",
            "maximum_marks": 1.0,
        }
        res = self.validator.validate(data, QuestionType.MCQ)
        self.assertFalse(res.is_valid)
        self.assertTrue(any("exactly 4 options" in err.lower() for err in res.errors))

    def test_mcq_correct_answer_not_in_options(self):
        data = {
            "question_text": "In which year did the storming of the Bastille occur?",
            "options": ["1789", "1791", "1793", "1799"],
            "correct_answer": "1815",
            "explanation": "The Bastille was stormed in 1789.",
            "chapter": "The French Revolution",
            "maximum_marks": 1.0,
        }
        res = self.validator.validate(data, QuestionType.MCQ)
        self.assertFalse(res.is_valid)
        self.assertTrue(any("does not match" in err.lower() for err in res.errors))

    def test_mcq_invalid_marks(self):
        data = {
            "question_text": "In which year did the storming of the Bastille occur?",
            "options": ["1789", "1791", "1793", "1799"],
            "correct_answer": "1789",
            "explanation": "The Bastille was stormed in 1789.",
            "chapter": "The French Revolution",
            "maximum_marks": -1.0,
        }
        res = self.validator.validate(data, QuestionType.MCQ)
        self.assertFalse(res.is_valid)
        self.assertTrue(any("greater than zero" in err.lower() for err in res.errors))

    def test_valid_subjective_data(self):
        data = {
            "question_text": "Explain the significance of the Tennis Court Oath in the French Revolution.",
            "question_type": "Short Answer",
            "expected_answer": "On 20 June 1789, the Third Estate delegates declared themselves a National Assembly and swore not to disperse until a constitution was drafted.",
            "marking_rubric": [
                {
                    "point": "Date and venue: 20 June 1789 in the indoor tennis court at Versailles",
                    "allocated_marks": 1.0,
                },
                {
                    "point": "Declaration: Proclaimed themselves as the National Assembly",
                    "allocated_marks": 1.0,
                },
                {
                    "point": "Pledge: Vowed not to disperse until drafting a constitution limiting monarch's powers",
                    "allocated_marks": 1.0,
                },
            ],
            "maximum_marks": 3.0,
            "chapter": "The French Revolution",
        }
        res = self.validator.validate(data, QuestionType.SHORT_ANSWER)
        self.assertTrue(res.is_valid)
        self.assertEqual(res.status, ValidationStatus.VALID)
        self.assertIsNotNone(res.validated_question)

    def test_subjective_rubric_sum_mismatch(self):
        data = {
            "question_text": "Explain the significance of the Tennis Court Oath.",
            "question_type": "Short Answer",
            "expected_answer": "Valid expected answer text here.",
            "marking_rubric": [
                {"point": "Point 1", "allocated_marks": 1.0},
                {"point": "Point 2", "allocated_marks": 1.0},
            ],
            "maximum_marks": 3.0,  # Sum is 2.0, max is 3.0
            "chapter": "The French Revolution",
        }
        res = self.validator.validate(data, QuestionType.SHORT_ANSWER)
        self.assertFalse(res.is_valid)
        self.assertTrue(any("does not match question maximum_marks" in err.lower() for err in res.errors))


if __name__ == "__main__":
    unittest.main()
