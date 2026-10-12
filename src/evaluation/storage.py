import hashlib
import json
import os
import sqlite3
from typing import List, Optional

from .models import AnswerEvaluationResult


class EvaluationStorage:
    """
    Persists evaluation records to a local SQLite database, keeping them decoupled
    from the question bank. Supports idempotency and prevents duplicate submissions.
    """

    def __init__(self, db_path: Optional[str] = None):
        if db_path:
            self.db_path = os.path.abspath(db_path)
        else:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            self.db_path = os.path.join(base_dir, "data", "evaluations.db")

        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS evaluation_results (
                    evaluation_id TEXT PRIMARY KEY,
                    submission_hash TEXT,
                    question_id TEXT NOT NULL,
                    student_id TEXT NOT NULL,
                    awarded_marks REAL NOT NULL,
                    maximum_marks REAL NOT NULL,
                    evaluation_status TEXT NOT NULL,
                    teacher_review_required INTEGER NOT NULL,
                    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    full_result_json TEXT NOT NULL
                )
            """)
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_sub_hash ON evaluation_results(submission_hash)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_qid ON evaluation_results(question_id)")
            conn.commit()

    def compute_hash(self, question_id: str, student_id: str, answer_text: str) -> str:
        content = f"{question_id.strip()}:{student_id.strip()}:{answer_text.strip()}"
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def find_duplicate(self, question_id: str, student_id: str, answer_text: str) -> Optional[AnswerEvaluationResult]:
        """
        Checks if an identical evaluation already exists to prevent duplicate submissions.
        """
        sub_hash = self.compute_hash(question_id, student_id, answer_text)
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT full_result_json FROM evaluation_results WHERE submission_hash = ? ORDER BY submitted_at DESC LIMIT 1",
                (sub_hash,),
            )
            row = cursor.fetchone()
            if row:
                try:
                    data = json.loads(row[0])
                    return AnswerEvaluationResult(**data)
                except Exception:
                    return None
        return None

    def save_result(self, result: AnswerEvaluationResult, student_id: str = "student_001") -> bool:
        """
        Saves a validated evaluation result record with deduplication.
        """
        sub_hash = self.compute_hash(result.question_id, student_id, result.student_submitted_answer)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO evaluation_results (
                    evaluation_id,
                    submission_hash,
                    question_id,
                    student_id,
                    awarded_marks,
                    maximum_marks,
                    evaluation_status,
                    teacher_review_required,
                    full_result_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result.evaluation_id,
                sub_hash,
                result.question_id,
                student_id,
                result.awarded_marks,
                result.maximum_marks,
                result.evaluation_status.value,
                1 if result.teacher_review_required else 0,
                result.model_dump_json(),
            ))
            conn.commit()
        return True

    def get_result(self, evaluation_id: str) -> Optional[AnswerEvaluationResult]:
        """
        Fetches an evaluation by its unique evaluation ID.
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT full_result_json FROM evaluation_results WHERE evaluation_id = ?",
                (evaluation_id,),
            )
            row = cursor.fetchone()
            if row:
                data = json.loads(row[0])
                return AnswerEvaluationResult(**data)
        return None

    def list_results_for_question(self, question_id: str) -> List[AnswerEvaluationResult]:
        """
        Returns all evaluation attempts for a specific question.
        """
        results = []
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT full_result_json FROM evaluation_results WHERE question_id = ? ORDER BY submitted_at DESC",
                (question_id,),
            )
            for row in cursor.fetchall():
                try:
                    data = json.loads(row[0])
                    results.append(AnswerEvaluationResult(**data))
                except Exception:
                    continue
        return results

    def list_all_results(self) -> List[AnswerEvaluationResult]:
        """
        Returns all stored evaluation attempts.
        """
        results = []
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT full_result_json FROM evaluation_results ORDER BY submitted_at DESC")
            for row in cursor.fetchall():
                try:
                    data = json.loads(row[0])
                    results.append(AnswerEvaluationResult(**data))
                except Exception:
                    continue
        return results
