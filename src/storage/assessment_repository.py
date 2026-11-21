"""
Assessment Repository Layer
Provides transactional SQLite storage and retrieval for Assessment sessions,
ordered question assignments, and student responses.
"""

import json
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.storage.database import Database
from src.models.assessment import (
    AssessmentType,
    AssessmentStatus,
    AssessmentSession,
    AssessmentQuestionView,
)
from src.models.question import Question, QuestionType, QuestionDifficulty, CognitiveLevel


class AssessmentRepository:
    """
    CRUD operations for Assessments and Student Answers.
    """

    def __init__(self, db: Database):
        self.db = db

    def create_assessment(
        self,
        assessment_id: str,
        student_id: str,
        assessment_type: AssessmentType,
        chapter_id: Optional[str],
        question_ids: List[str],
        total_marks: int,
    ) -> None:
        """
        Creates an assessment session and links assigned questions in a transaction.
        """
        with self.db.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO assessments (
                    assessment_id, student_id, assessment_type, chapter_id,
                    status, total_questions, total_marks, score, started_at
                ) VALUES (?, ?, ?, ?, 'IN_PROGRESS', ?, ?, 0.0, CURRENT_TIMESTAMP);
                """,
                (
                    assessment_id,
                    student_id,
                    assessment_type.value if hasattr(assessment_type, "value") else str(assessment_type),
                    chapter_id,
                    len(question_ids),
                    total_marks,
                ),
            )

            for order, qid in enumerate(question_ids, start=1):
                conn.execute(
                    """
                    INSERT INTO assessment_questions (assessment_id, question_id, question_order)
                    VALUES (?, ?, ?);
                    """,
                    (assessment_id, qid, order),
                )
            conn.commit()

    def get_student_answered_question_ids(self, student_id: str, only_correct: bool = True) -> set:
        """
        Returns a set of question IDs the student has previously answered.
        Used for deduplication so that mastered questions are never repeated.
        """
        with self.db.get_connection() as conn:
            if only_correct:
                rows = conn.execute(
                    "SELECT DISTINCT question_id FROM student_answers WHERE student_id = ? AND is_correct = 1",
                    (student_id,)
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT DISTINCT question_id FROM student_answers WHERE student_id = ?",
                    (student_id,)
                ).fetchall()
            return {r["question_id"] for r in rows}

    def get_assessment(self, assessment_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetches an assessment header row.
        """
        with self.db.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM assessments WHERE assessment_id = ?;", (assessment_id,)
            ).fetchone()
            if not row:
                return None
            return dict(row)

    def get_assessment_question_ids(self, assessment_id: str) -> List[str]:
        """
        Returns question IDs assigned to an assessment in presentation order.
        """
        with self.db.get_connection() as conn:
            rows = conn.execute(
                """
                SELECT question_id FROM assessment_questions
                WHERE assessment_id = ?
                ORDER BY question_order ASC;
                """,
                (assessment_id,),
            ).fetchall()
            return [r[0] for r in rows]

    def record_student_answer(
        self,
        answer_id: str,
        assessment_id: str,
        student_id: str,
        question_id: str,
        submitted_answer: Dict[str, Any],
        is_correct: bool,
        marks_awarded: float,
        feedback: str,
        detected_misconceptions: List[str],
        time_spent_seconds: int = 0,
    ) -> None:
        """
        Inserts or updates a student answer attempt for an assessment.
        """
        with self.db.get_connection() as conn:
            conn.execute(
                """
                INSERT INTO student_answers (
                    answer_id, assessment_id, student_id, question_id,
                    submitted_answer_json, is_correct, marks_awarded,
                    evaluation_feedback, detected_misconceptions_json,
                    time_spent_seconds, submitted_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(assessment_id, question_id) DO UPDATE SET
                    submitted_answer_json = excluded.submitted_answer_json,
                    is_correct = excluded.is_correct,
                    marks_awarded = excluded.marks_awarded,
                    evaluation_feedback = excluded.evaluation_feedback,
                    detected_misconceptions_json = excluded.detected_misconceptions_json,
                    time_spent_seconds = excluded.time_spent_seconds,
                    submitted_at = CURRENT_TIMESTAMP;
                """,
                (
                    answer_id,
                    assessment_id,
                    student_id,
                    question_id,
                    json.dumps(submitted_answer),
                    1 if is_correct else 0,
                    marks_awarded,
                    feedback,
                    json.dumps(detected_misconceptions),
                    time_spent_seconds,
                ),
            )
            conn.commit()

    def get_answers_for_assessment(self, assessment_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves all recorded answers for an assessment session.
        """
        with self.db.get_connection() as conn:
            rows = conn.execute(
                """
                SELECT * FROM student_answers
                WHERE assessment_id = ?
                ORDER BY submitted_at ASC;
                """,
                (assessment_id,),
            ).fetchall()
            results = []
            for r in rows:
                item = dict(r)
                item["submitted_answer"] = json.loads(item["submitted_answer_json"]) if item.get("submitted_answer_json") else {}
                item["detected_misconceptions"] = json.loads(item["detected_misconceptions_json"]) if item.get("detected_misconceptions_json") else []
                results.append(item)
            return results

    def finalize_assessment(self, assessment_id: str, score: float) -> None:
        """
        Marks an assessment as COMPLETED / EVALUATED and records final score.
        """
        with self.db.get_connection() as conn:
            conn.execute(
                """
                UPDATE assessments
                SET status = 'EVALUATED',
                    score = ?,
                    completed_at = CURRENT_TIMESTAMP
                WHERE assessment_id = ?;
                """,
                (score, assessment_id),
            )
            conn.commit()

    def get_student_assessment_history(self, student_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retrieves recent assessment records for a student.
        """
        with self.db.get_connection() as conn:
            rows = conn.execute(
                """
                SELECT a.*, c.name as chapter_name
                FROM assessments a
                LEFT JOIN chapters c ON a.chapter_id = c.chapter_id
                WHERE a.student_id = ?
                ORDER BY a.started_at DESC
                LIMIT ?;
                """,
                (student_id, limit),
            ).fetchall()
            return [dict(r) for r in rows]
