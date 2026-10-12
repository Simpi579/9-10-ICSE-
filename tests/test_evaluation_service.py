"""
Unit and integration tests for AnswerEvaluationService covering all 10 evaluation scenarios.
"""

import json
import os
import sys
import unittest
from unittest.mock import MagicMock

# Make sure Python can find our source code
current_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(current_dir, '..', 'src')
sys.path.append(src_dir)

from evaluation.evaluator import AnswerEvaluationService
from evaluation.models import EvaluationRequest, EvaluationStatus
from repository.question_repo import QuestionRepository


class TestAnswerEvaluationService(unittest.TestCase):

    def setUp(self):
        self.repo = QuestionRepository()
        self.service = AnswerEvaluationService(repository=self.repo)

    def test_01_fully_correct_answer(self):
        """1. Fully correct answer receives full marks and clear criteria breakdown."""
        student_ans = (
            "The subsistence crisis in France was caused by a rapid increase in population from 23 million to 28 million, "
            "which caused huge demand for food grains. The production could not keep pace so the price of bread rose rapidly, "
            "while workers' fixed wages could not cope with inflation. Furthermore, frequent droughts and hail destroyed harvests."
        )
        req = EvaluationRequest(question_id="CBSE-HIST-09-001", student_answer=student_ans)
        result = self.service.evaluate(req)

        self.assertEqual(result.awarded_marks, 3.0)
        self.assertEqual(result.maximum_marks, 3.0)
        self.assertEqual(result.evaluation_status, EvaluationStatus.EVALUATED)
        self.assertFalse(result.teacher_review_required)
        self.assertGreaterEqual(len(result.correct_concepts_identified), 2)
        self.assertEqual(len(result.factual_errors), 0)

    def test_02_partially_correct_answer(self):
        """2. Partially correct answer receives partial credit and identifies missing points."""
        # Only mentions population increase; leaves out bread prices and hail/weather
        student_ans = "The population of France increased very quickly from 23 million to 28 million so there was more demand for grains."
        req = EvaluationRequest(question_id="CBSE-HIST-09-001", student_answer=student_ans)
        result = self.service.evaluate(req)

        self.assertGreater(result.awarded_marks, 0.0)
        self.assertLess(result.awarded_marks, 3.0)
        self.assertGreater(len(result.missing_concepts), 0)

    def test_03_valid_answer_different_wording(self):
        """3. Valid answer written with different vocabulary is recognized without keyword matching."""
        student_ans = (
            "A huge surge in the number of citizens created severe grain shortages across the kingdom. "
            "The cost of standard loaves of bread skyrocketed while daily laborer earnings did not increase, "
            "and severe climatic conditions like frost and dry spells ruined agricultural output."
        )
        req = EvaluationRequest(question_id="CBSE-HIST-09-001", student_answer=student_ans)
        result = self.service.evaluate(req)

        # Should award high/full marks for genuine conceptual understanding
        self.assertGreaterEqual(result.awarded_marks, 2.0)
        self.assertEqual(result.evaluation_status, EvaluationStatus.EVALUATED)

    def test_04_answer_containing_factual_errors(self):
        """4. Answer containing historical inaccuracies identifies claims and corrections."""
        student_ans = "Hitler stormed the Bastille in 1945 because bread was expensive."
        req = EvaluationRequest(question_id="CBSE-HIST-09-001", student_answer=student_ans)
        result = self.service.evaluate(req)

        self.assertGreater(len(result.factual_errors), 0)
        # Check that error correction is evidence-based
        error = result.factual_errors[0]
        self.assertIn("Hitler", error.student_claim)

    def test_05_mixed_correct_and_incorrect_points(self):
        """5. Answer containing both correct facts and historical errors awards partial marks without crashing."""
        student_ans = (
            "The population increased from 23 million to 28 million leading to high demand for food grains, "
            "but Hitler invaded Paris in 1945 to take over the bakeries."
        )
        req = EvaluationRequest(question_id="CBSE-HIST-09-001", student_answer=student_ans)
        result = self.service.evaluate(req)

        self.assertGreater(result.awarded_marks, 0.0)
        self.assertLess(result.awarded_marks, 3.0)
        self.assertGreater(len(result.factual_errors), 0)
        self.assertGreater(len(result.correct_concepts_identified), 0)

    def test_06_blank_answer(self):
        """6. Blank answer is handled immediately without calling the AI and receives 0 marks."""
        req = EvaluationRequest(question_id="CBSE-HIST-09-001", student_answer="   ")
        result = self.service.evaluate(req)

        self.assertEqual(result.awarded_marks, 0.0)
        self.assertEqual(result.evaluation_status, EvaluationStatus.BLANK_ANSWER)
        self.assertFalse(result.teacher_review_required)
        self.assertIn("blank", result.feedback.lower())

    def test_07_unverified_or_missing_rubric(self):
        """7. Question without a verified rubric is explicitly marked as provisional with review required."""
        # CBSE-HIST-09-004 has rubric_status = UNVERIFIED
        req = EvaluationRequest(
            question_id="CBSE-HIST-09-004",
            student_answer="Hitler pulled Germany out of League of Nations and reoccupied Rhineland in 1936.",
        )
        result = self.service.evaluate(req)

        self.assertEqual(result.evaluation_status, EvaluationStatus.PROVISIONAL)
        self.assertTrue(result.teacher_review_required)
        self.assertIn("unverified", result.review_reason.lower())

    def test_08_malformed_gemini_response(self):
        """8. Malformed or unparseable Gemini JSON produces a safe error result without crashing."""
        mock_client = MagicMock()
        mock_client.generate_json.return_value = "{malformed_json_response: true,"
        svc = AnswerEvaluationService(repository=self.repo, client=mock_client)

        req = EvaluationRequest(question_id="CBSE-HIST-09-001", student_answer="Some answer")
        result = svc.evaluate(req)

        self.assertEqual(result.evaluation_status, EvaluationStatus.ERROR)
        self.assertTrue(result.teacher_review_required)
        self.assertIn("malformed", result.review_reason.lower())

    def test_09_awarded_mark_exceeding_maximum_clamped(self):
        """9. AI responses attempting to award marks beyond question maximum marks are strictly clamped."""
        mock_client = MagicMock()
        # Mock returns 10 marks on a 3-mark question!
        mock_client.generate_json.return_value = json.dumps({
            "awarded_marks": 10.0,
            "criterion_wise_marks": [
                {"criterion": "Crit 1", "maximum_marks": 1.0, "awarded_marks": 1.0, "feedback": "Good"},
                {"criterion": "Crit 2", "maximum_marks": 1.0, "awarded_marks": 1.0, "feedback": "Good"},
                {"criterion": "Crit 3", "maximum_marks": 1.0, "awarded_marks": 1.0, "feedback": "Good"}
            ],
            "correct_concepts_identified": ["All concepts"],
            "missing_concepts": [],
            "factual_errors": [],
            "feedback": "Outstanding answer.",
            "improvement_suggestions": [],
            "confidence_score": 0.95
        })
        svc = AnswerEvaluationService(repository=self.repo, client=mock_client)

        req = EvaluationRequest(question_id="CBSE-HIST-09-001", student_answer="Complete answer")
        result = svc.evaluate(req)

        # Server-side validation MUST cap the marks at 3.0
        self.assertLessEqual(result.awarded_marks, 3.0)
        self.assertEqual(result.maximum_marks, 3.0)

    def test_10_gemini_api_failure_or_timeout(self):
        """10. Network timeouts and API exceptions are handled cleanly without unhandled crashes."""
        mock_client = MagicMock()
        mock_client.generate_json.side_effect = RuntimeError("503 Service Unavailable: Gateway Timeout")
        svc = AnswerEvaluationService(repository=self.repo, client=mock_client)

        req = EvaluationRequest(question_id="CBSE-HIST-09-001", student_answer="Some answer")
        result = svc.evaluate(req)

        self.assertEqual(result.evaluation_status, EvaluationStatus.ERROR)
        self.assertTrue(result.teacher_review_required)
        self.assertIn("timeout", result.review_reason.lower())


if __name__ == "__main__":
    unittest.main()
