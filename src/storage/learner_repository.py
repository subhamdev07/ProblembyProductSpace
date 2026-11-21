"""
Learner Model Repository Layer
Provides transactional storage and tracking for Student profiles,
Concept-wise mastery scores, and diagnostic misconception evidence.
"""

import uuid
from typing import List, Dict, Any, Optional

from src.storage.database import Database
from src.models.learner import (
    ConceptMasteryStatus,
    ConceptMasteryItem,
    StudentProfile,
)


class LearnerRepository:
    """
    CRUD and analytics for student mastery and diagnostic tracking.
    """

    def __init__(self, db: Database):
        self.db = db

    def get_or_create_student(
        self,
        student_id: str = "STU-001",
        name: str = "Aarav Sharma",
        grade: int = 10,
    ) -> StudentProfile:
        """
        Retrieves existing student profile or creates a default demo student.
        """
        with self.db.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM students WHERE student_id = ?;", (student_id,)
            ).fetchone()
            if row:
                return StudentProfile(
                    student_id=row["student_id"],
                    name=row["name"],
                    grade=row["grade"],
                    created_at=str(row["created_at"]) if row["created_at"] else None,
                )

            conn.execute(
                "INSERT INTO students (student_id, name, grade) VALUES (?, ?, ?);",
                (student_id, name, grade),
            )
            conn.commit()
            return StudentProfile(student_id=student_id, name=name, grade=grade)

    def get_student(self, student_id: str) -> Optional[StudentProfile]:
        """
        Retrieves existing student profile by ID, or None if not found.
        """
        with self.db.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM students WHERE student_id = ?;", (student_id,)
            ).fetchone()
            if not row:
                return None
            return StudentProfile(
                student_id=row["student_id"],
                name=row["name"],
                grade=row["grade"],
                created_at=str(row["created_at"]) if row["created_at"] else None,
            )

    def get_concept_mastery(
        self, student_id: str, concept_id: str
    ) -> Optional[ConceptMasteryItem]:
        """
        Fetches mastery state for a specific concept node.
        """
        with self.db.get_connection() as conn:
            row = conn.execute(
                """
                SELECT m.*, c.name as concept_name, c.canonical_name, c.chapter_id, c.topic_id
                FROM learner_concept_mastery m
                JOIN concepts c ON m.concept_id = c.concept_id
                WHERE m.student_id = ? AND m.concept_id = ?;
                """,
                (student_id, concept_id),
            ).fetchone()
            if not row:
                return None
            return self._row_to_mastery_item(row)

    def get_all_concept_mastery(
        self, student_id: str, chapter_id: Optional[str] = None
    ) -> List[ConceptMasteryItem]:
        """
        Retrieves mastery states for all concepts (joining with all curriculum concepts
        so unassessed concepts appear as NOT_ASSESSED).
        """
        sql = """
        SELECT 
            c.concept_id,
            c.name as concept_name,
            c.canonical_name,
            c.chapter_id,
            c.topic_id,
            COALESCE(m.mastery_score, 0.0) as mastery_score,
            COALESCE(m.confidence_score, 0.5) as confidence_score,
            COALESCE(m.total_attempts, 0) as total_attempts,
            COALESCE(m.correct_attempts, 0) as correct_attempts,
            COALESCE(m.incorrect_attempts, 0) as incorrect_attempts,
            m.last_attempted_at
        FROM concepts c
        LEFT JOIN learner_concept_mastery m 
            ON c.concept_id = m.concept_id AND m.student_id = ?
        """
        params = [student_id]
        if chapter_id:
            sql += " WHERE c.chapter_id = ?"
            params.append(chapter_id)
        sql += " ORDER BY c.chapter_id, c.concept_id;"

        with self.db.get_connection() as conn:
            rows = conn.execute(sql, tuple(params)).fetchall()
            return [self._row_to_mastery_item(r) for r in rows]

    def get_weakest_concepts(
        self, student_id: str, limit: int = 5, chapter_id: Optional[str] = None
    ) -> List[ConceptMasteryItem]:
        """
        Retrieves the student's weakest assessed concepts, sorted ascending by mastery score.
        """
        all_items = self.get_all_concept_mastery(student_id, chapter_id=chapter_id)
        assessed = [m for m in all_items if m.total_attempts > 0]
        assessed.sort(key=lambda m: m.mastery_score)
        return assessed[:limit]

    def update_mastery(
        self,
        student_id: str,
        concept_id: str,
        is_correct: bool,
        difficulty_multiplier: float = 1.0,
    ) -> ConceptMasteryItem:
        """
        Updates concept mastery using an explainable Bayesian/evidence update formula:
        - Correct answer: +0.25 * difficulty_multiplier (capped at 1.0)
        - Incorrect answer: -0.20 * difficulty_multiplier (floored at 0.0)
        - Confidence score scales asymptotically with total attempts: 1 - 0.5^attempts
        """
        self.get_or_create_student(student_id)
        with self.db.get_connection() as conn:
            current = conn.execute(
                """
                SELECT * FROM learner_concept_mastery
                WHERE student_id = ? AND concept_id = ?;
                """,
                (student_id, concept_id),
            ).fetchone()

            if current:
                attempts = current["total_attempts"] + 1
                correct = current["correct_attempts"] + (1 if is_correct else 0)
                incorrect = current["incorrect_attempts"] + (0 if is_correct else 1)
                cur_score = current["mastery_score"]
            else:
                attempts = 1
                correct = 1 if is_correct else 0
                incorrect = 0 if is_correct else 1
                cur_score = 0.3 if is_correct else 0.1

            if current:
                delta = (0.25 if is_correct else -0.20) * difficulty_multiplier
                new_score = max(0.0, min(1.0, round(cur_score + delta, 3)))
            else:
                new_score = 0.5 if is_correct else 0.1

            confidence = round(1.0 - (0.5 ** attempts), 3)

            mastery_id = current["mastery_id"] if current else f"MST-{uuid.uuid4().hex[:8]}"

            conn.execute(
                """
                INSERT INTO learner_concept_mastery (
                    mastery_id, student_id, concept_id, mastery_score,
                    confidence_score, total_attempts, correct_attempts,
                    incorrect_attempts, last_attempted_at, last_updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT(student_id, concept_id) DO UPDATE SET
                    mastery_score = excluded.mastery_score,
                    confidence_score = excluded.confidence_score,
                    total_attempts = excluded.total_attempts,
                    correct_attempts = excluded.correct_attempts,
                    incorrect_attempts = excluded.incorrect_attempts,
                    last_attempted_at = CURRENT_TIMESTAMP,
                    last_updated_at = CURRENT_TIMESTAMP;
                """,
                (
                    mastery_id,
                    student_id,
                    concept_id,
                    new_score,
                    confidence,
                    attempts,
                    correct,
                    incorrect,
                ),
            )
            conn.commit()

        return self.get_concept_mastery(student_id, concept_id)

    def record_misconceptions(
        self, student_id: str, concept_id: str, misconception_tags: List[str]
    ) -> None:
        """
        Logs or increments observed student misconception evidence.
        """
        if not misconception_tags:
            return

        with self.db.get_connection() as conn:
            for tag in misconception_tags:
                rec_id = f"MIS-{uuid.uuid4().hex[:8]}"
                conn.execute(
                    """
                    INSERT INTO student_misconceptions (
                        misconception_record_id, student_id, concept_id,
                        misconception_tag, status, evidence_count, last_observed_at
                    ) VALUES (?, ?, ?, ?, 'SUSPECTED', 1, CURRENT_TIMESTAMP)
                    ON CONFLICT(student_id, concept_id, misconception_tag) DO UPDATE SET
                        evidence_count = evidence_count + 1,
                        status = CASE WHEN evidence_count + 1 >= 2 THEN 'CONFIRMED' ELSE status END,
                        last_observed_at = CURRENT_TIMESTAMP;
                    """,
                    (rec_id, student_id, concept_id, tag),
                )
            conn.commit()

    def get_student_misconceptions(self, student_id: str) -> List[Dict[str, Any]]:
        """
        Retrieves all recorded misconceptions for a student.
        """
        with self.db.get_connection() as conn:
            rows = conn.execute(
                """
                SELECT m.*, c.name as concept_name
                FROM student_misconceptions m
                JOIN concepts c ON m.concept_id = c.concept_id
                WHERE m.student_id = ?
                ORDER BY m.evidence_count DESC, m.last_observed_at DESC;
                """,
                (student_id,),
            ).fetchall()
            return [dict(r) for r in rows]

    def _row_to_mastery_item(self, row: Any) -> ConceptMasteryItem:
        r = dict(row)
        attempts = r.get("total_attempts", 0)
        score = r.get("mastery_score", 0.0)

        if attempts == 0:
            status = ConceptMasteryStatus.NOT_ASSESSED
        elif score < 0.5:
            status = ConceptMasteryStatus.DEVELOPING
        elif score < 0.8:
            status = ConceptMasteryStatus.IMPROVING
        else:
            status = ConceptMasteryStatus.STRONG

        return ConceptMasteryItem(
            concept_id=r["concept_id"],
            concept_name=r["concept_name"],
            canonical_name=r.get("canonical_name"),
            chapter_id=r["chapter_id"],
            topic_id=r["topic_id"],
            mastery_score=score,
            confidence_score=r.get("confidence_score", 0.5),
            status=status,
            total_attempts=attempts,
            correct_attempts=r.get("correct_attempts", 0),
            incorrect_attempts=r.get("incorrect_attempts", 0),
            last_attempted_at=str(r["last_attempted_at"]) if r.get("last_attempted_at") else None,
        )
