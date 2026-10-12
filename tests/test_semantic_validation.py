"""
Unit tests for Semantic and Syllabus Validator.
Covers CBSE Class 9 History and configurable test cases (e.g. ICSE Class 9 Computer Applications).
"""

import unittest
from schema.enums import Board, ClassGrade, Subject, QuestionType, ValidationStatus
from schema.models import MCQQuestion, SubjectiveQuestion, RubricCriterion
from validation.semantic import SemanticValidator


class TestSemanticValidator(unittest.TestCase):

    def setUp(self):
        self.validator = SemanticValidator(strict_syllabus=True)

    def test_cbse_class_9_history_valid_chapter(self):
        mcq = MCQQuestion(
            board=Board.CBSE,
            class_grade=ClassGrade.CLASS_9,
            subject=Subject.HISTORY,
            chapter="The French Revolution",
            question_text="Who wrote the influential pamphlet called 'What is the Third Estate'?",
            options=["Abbé Sieyès", "Mirabeau", "Robespierre", "Rousseau"],
            correct_answer="Abbé Sieyès",
            explanation="Abbé Sieyès, originally a priest, wrote the pamphlet 'What is the Third Estate?'",
            maximum_marks=1.0,
        )
        res = self.validator.validate(mcq)
        self.assertTrue(res.is_valid)
        self.assertEqual(res.status, ValidationStatus.VALID)

    def test_cbse_class_9_history_mismatched_chapter(self):
        mcq = MCQQuestion(
            board=Board.CBSE,
            class_grade=ClassGrade.CLASS_9,
            subject=Subject.HISTORY,
            chapter="Chemical Reactions and Equations",  # Science chapter, invalid for History!
            question_text="Which gas is released during photosynthesis in plants?",
            options=["Oxygen", "Carbon Dioxide", "Nitrogen", "Hydrogen"],
            correct_answer="Oxygen",
            explanation="Oxygen is released.",
            maximum_marks=1.0,
        )
        res = self.validator.validate(mcq)
        self.assertFalse(res.is_valid)
        self.assertEqual(res.status, ValidationStatus.INVALID)
        self.assertTrue(any("not recognized for CBSE Class 9 History" in err for err in res.errors))

    def test_icse_class_9_computer_applications_configurable_case(self):
        """
        Configurable secondary test case: ICSE Class 9 Computer Applications.
        Ensures curriculum registry accurately handles other syllabus tracks.
        """
        mcq = MCQQuestion(
            board=Board.ICSE,
            class_grade=ClassGrade.CLASS_9,
            subject=Subject.COMPUTER_APPLICATIONS,
            chapter="Operators in Java",
            question_text="Which of the following is a ternary operator in Java?",
            options=["? :", "&&", "++", "=="],
            correct_answer="? :",
            explanation="The ternary conditional operator in Java has the syntax condition ? exp1 : exp2.",
            maximum_marks=1.0,
        )
        res = self.validator.validate(mcq)
        self.assertTrue(res.is_valid)
        self.assertEqual(res.status, ValidationStatus.VALID)

    def test_icse_computer_applications_rejects_unrelated_chapter(self):
        mcq = MCQQuestion(
            board=Board.ICSE,
            class_grade=ClassGrade.CLASS_9,
            subject=Subject.COMPUTER_APPLICATIONS,
            chapter="Nazism and the Rise of Hitler",  # History chapter passed to Computer Applications
            question_text="In which year was Hitler appointed Chancellor of Germany?",
            options=["1933", "1939", "1919", "1945"],
            correct_answer="1933",
            explanation="Hitler was appointed Chancellor on 30 January 1933.",
            maximum_marks=1.0,
        )
        res = self.validator.validate(mcq)
        self.assertFalse(res.is_valid)
        self.assertTrue(any("not recognized for ICSE Class 9 Computer Applications" in err for err in res.errors))

    def test_detects_tautology_in_mcq(self):
        mcq = MCQQuestion(
            board=Board.CBSE,
            class_grade=ClassGrade.CLASS_9,
            subject=Subject.HISTORY,
            chapter="The French Revolution",
            question_text="The Bastille",
            options=["The Bastille", "Versailles", "Tuileries", "Louvre"],
            correct_answer="The Bastille",
            explanation="Valid historical explanation.",
            maximum_marks=1.0,
        )
        res = self.validator.validate(mcq)
        self.assertFalse(res.is_valid)
        self.assertTrue(any("tautology" in err.lower() for err in res.errors))


if __name__ == "__main__":
    unittest.main()
