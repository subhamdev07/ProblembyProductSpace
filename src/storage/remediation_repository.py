"""
Remediation & Spaced Repetition Repository
Manages student misconceptions, revision schedules, remediation logs, and embeddings.
"""

import json
import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional

from src.storage.database import Database
from src.models.remediation import (
    MisconceptionStatus,
    StudentMisconceptionItem,
)
from src.models.spaced_repetition import (
    ReviewStatus,
    SpacedRepetitionItem,
)


class RemediationRepository:
    def __init__(self, db: Database):
        self.db = db

    # --------------------------------------------------------------------------
    # 1. Misconception Persistence
    # --------------------------------------------------------------------------
    def record_misconception_evidence(
        self,
        student_id: str,
        concept_id: str,
        misconception_tag: str,
        evidence_text: Optional[str] = None,
        force_confirmed: bool = False
    ) -> StudentMisconceptionItem:
        """
        Records evidence of a misconception.
        - First occurrence: marked SUSPECTED (unless force_confirmed is True).
        - Second or repeated occurrence: promoted to CONFIRMED.
        """
        now_str = datetime.now(timezone.utc).isoformat()

        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT misconception_record_id, status, evidence_count, evidence_text
                FROM student_misconceptions
                WHERE student_id = ? AND concept_id = ? AND misconception_tag = ?;
                """,
                (student_id, concept_id, misconception_tag)
            )
            existing = cur.fetchone()

            if existing:
                rec_id = existing["misconception_record_id"]
                new_count = existing["evidence_count"] + 1
                # If already SUSPECTED and seen again, promote to CONFIRMED
                if existing["status"] == MisconceptionStatus.RESOLVED.value:
                    new_status = MisconceptionStatus.SUSPECTED.value
                else:
                    new_status = MisconceptionStatus.CONFIRMED.value if (new_count >= 2 or force_confirmed) else existing["status"]

                combined_evidence = (existing["evidence_text"] or "")
                if evidence_text and evidence_text not in combined_evidence:
                    combined_evidence = f"{combined_evidence} | {evidence_text}".strip(" |")

                cur.execute(
                    """
                    UPDATE student_misconceptions
                    SET status = ?, evidence_count = ?, evidence_text = ?, last_observed_at = ?
                    WHERE misconception_record_id = ?;
                    """,
                    (new_status, new_count, combined_evidence, now_str, rec_id)
                )
                conn.commit()

                return StudentMisconceptionItem(
                    misconception_record_id=rec_id,
                    student_id=student_id,
                    concept_id=concept_id,
                    misconception_tag=misconception_tag,
                    status=MisconceptionStatus(new_status),
                    evidence_count=new_count,
                    evidence_text=combined_evidence,
                    last_observed_at=now_str
                )
            else:
                rec_id = f"MISC-{uuid.uuid4().hex[:8]}"
                initial_status = MisconceptionStatus.CONFIRMED.value if force_confirmed else MisconceptionStatus.SUSPECTED.value
                cur.execute(
                    """
                    INSERT INTO student_misconceptions (
                        misconception_record_id, student_id, concept_id,
                        misconception_tag, status, evidence_count, evidence_text, last_observed_at
                    ) VALUES (?, ?, ?, ?, ?, 1, ?, ?);
                    """,
                    (rec_id, student_id, concept_id, misconception_tag, initial_status, evidence_text or "", now_str)
                )
                conn.commit()

                return StudentMisconceptionItem(
                    misconception_record_id=rec_id,
                    student_id=student_id,
                    concept_id=concept_id,
                    misconception_tag=misconception_tag,
                    status=MisconceptionStatus(initial_status),
                    evidence_count=1,
                    evidence_text=evidence_text,
                    last_observed_at=now_str
                )

    def resolve_misconceptions_for_concept(self, student_id: str, concept_id: str) -> int:
        """Marks any active misconceptions on this concept as RESOLVED upon proven correct understanding."""
        now_str = datetime.now(timezone.utc).isoformat()
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE student_misconceptions
                SET status = 'RESOLVED', last_observed_at = ?
                WHERE student_id = ? AND concept_id = ? AND status != 'RESOLVED';
                """,
                (now_str, student_id, concept_id)
            )
            affected = cur.rowcount
            conn.commit()
            return affected

    def get_student_misconceptions(
        self,
        student_id: str,
        status: Optional[MisconceptionStatus] = None
    ) -> List[StudentMisconceptionItem]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            query = """
                SELECT sm.*, c.name as concept_name, c.chapter_id
                FROM student_misconceptions sm
                LEFT JOIN concepts c ON sm.concept_id = c.concept_id
                WHERE sm.student_id = ?
            """
            params = [student_id]
            if status:
                query += " AND sm.status = ?"
                params.append(status.value)
            query += " ORDER BY sm.last_observed_at DESC;"

            cur.execute(query, params)
            rows = cur.fetchall()

            items = []
            for r in rows:
                items.append(
                    StudentMisconceptionItem(
                        misconception_record_id=r["misconception_record_id"],
                        student_id=r["student_id"],
                        concept_id=r["concept_id"],
                        concept_name=r["concept_name"] or r["concept_id"],
                        chapter_id=r["chapter_id"] or "CH01",
                        misconception_tag=r["misconception_tag"],
                        status=MisconceptionStatus(r["status"]),
                        evidence_count=r["evidence_count"],
                        evidence_text=r["evidence_text"],
                        last_observed_at=r["last_observed_at"]
                    )
                )
            return items

    def get_all_misconceptions_summary(self) -> List[Dict[str, Any]]:
        """Returns cohort-wide misconception distribution for teacher views."""
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT
                    sm.misconception_tag,
                    sm.concept_id,
                    c.name as concept_name,
                    COUNT(DISTINCT sm.student_id) as affected_students,
                    SUM(CASE WHEN sm.status = 'CONFIRMED' THEN 1 ELSE 0 END) as confirmed_count,
                    SUM(CASE WHEN sm.status = 'SUSPECTED' THEN 1 ELSE 0 END) as suspected_count,
                    SUM(CASE WHEN sm.status = 'RESOLVED' THEN 1 ELSE 0 END) as resolved_count
                FROM student_misconceptions sm
                LEFT JOIN concepts c ON sm.concept_id = c.concept_id
                GROUP BY sm.misconception_tag, sm.concept_id
                ORDER BY affected_students DESC, confirmed_count DESC;
                """
            )
            rows = cur.fetchall()
            return [dict(r) for r in rows]

    # --------------------------------------------------------------------------
    # 2. Spaced Repetition Persistence
    # --------------------------------------------------------------------------
    def schedule_or_update_revision(
        self,
        student_id: str,
        concept_id: str,
        interval_days: int = 1,
        ease_factor: float = 2.5,
        last_result: Optional[str] = "NOT_REVIEWED",
        current_mastery: float = 0.0
    ) -> SpacedRepetitionItem:
        now = datetime.now(timezone.utc)
        now_str = now.isoformat()
        next_review = now + timedelta(days=interval_days)
        next_review_str = next_review.isoformat()

        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT schedule_id, review_count FROM spaced_repetition_schedules
                WHERE student_id = ? AND concept_id = ?;
                """,
                (student_id, concept_id)
            )
            existing = cur.fetchone()

            if existing:
                sched_id = existing["schedule_id"]
                new_review_count = existing["review_count"] + (1 if last_result != "NOT_REVIEWED" else 0)
                cur.execute(
                    """
                    UPDATE spaced_repetition_schedules
                    SET last_reviewed_at = ?, next_review_at = ?, interval_days = ?,
                        ease_factor = ?, review_count = ?, last_result = ?,
                        current_mastery = ?, review_status = 'PENDING', updated_at = ?
                    WHERE schedule_id = ?;
                    """,
                    (now_str, next_review_str, interval_days, ease_factor, new_review_count, last_result, current_mastery, now_str, sched_id)
                )
            else:
                sched_id = f"REV-{uuid.uuid4().hex[:8]}"
                cur.execute(
                    """
                    INSERT INTO spaced_repetition_schedules (
                        schedule_id, student_id, concept_id, last_reviewed_at,
                        next_review_at, interval_days, ease_factor, review_count,
                        last_result, current_mastery, review_status, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?, 'PENDING', ?, ?);
                    """,
                    (sched_id, student_id, concept_id, now_str, next_review_str, interval_days, ease_factor, last_result, current_mastery, now_str, now_str)
                )
            conn.commit()

            # Retrieve concept details
            cur.execute("SELECT name, chapter_id FROM concepts WHERE concept_id = ?;", (concept_id,))
            c_row = cur.fetchone()
            concept_name = c_row["name"] if c_row else concept_id
            chapter_id = c_row["chapter_id"] if c_row else "CH01"

            return SpacedRepetitionItem(
                schedule_id=sched_id,
                student_id=student_id,
                concept_id=concept_id,
                concept_name=concept_name,
                chapter_id=chapter_id,
                last_reviewed_at=now_str,
                next_review_at=next_review_str,
                interval_days=interval_days,
                ease_factor=ease_factor,
                review_count=existing["review_count"] if existing else 0,
                last_result=last_result,
                current_mastery=current_mastery,
                review_status=ReviewStatus.PENDING,
                days_until_due=interval_days
            )

    def get_revision_schedules(self, student_id: str) -> List[SpacedRepetitionItem]:
        now = datetime.now(timezone.utc)
        now_str = now.isoformat()

        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT s.*, c.name as concept_name, c.chapter_id
                FROM spaced_repetition_schedules s
                LEFT JOIN concepts c ON s.concept_id = c.concept_id
                WHERE s.student_id = ?
                ORDER BY s.next_review_at ASC;
                """,
                (student_id,)
            )
            rows = cur.fetchall()

            items = []
            for r in rows:
                next_rev_dt = datetime.fromisoformat(r["next_review_at"])
                days_left = (next_rev_dt - now).days
                
                # Determine status dynamically
                if days_left < 0:
                    status = ReviewStatus.OVERDUE
                elif days_left == 0:
                    status = ReviewStatus.DUE
                else:
                    status = ReviewStatus.PENDING

                items.append(
                    SpacedRepetitionItem(
                        schedule_id=r["schedule_id"],
                        student_id=r["student_id"],
                        concept_id=r["concept_id"],
                        concept_name=r["concept_name"] or r["concept_id"],
                        chapter_id=r["chapter_id"] or "CH01",
                        last_reviewed_at=r["last_reviewed_at"],
                        next_review_at=r["next_review_at"],
                        interval_days=r["interval_days"],
                        ease_factor=r["ease_factor"],
                        review_count=r["review_count"],
                        last_result=r["last_result"],
                        current_mastery=r["current_mastery"],
                        review_status=status,
                        days_until_due=max(0, days_left)
                    )
                )
            return items

    # --------------------------------------------------------------------------
    # 3. Remediation Records Persistence
    # --------------------------------------------------------------------------
    def log_remediation_event(
        self,
        student_id: str,
        concept_id: str,
        prereq_id: Optional[str],
        gap_summary: str,
        ncert_ref: str,
        explanation: str,
        example: str,
        question_id: Optional[str],
        mastery_before: float
    ) -> str:
        rem_id = f"REM-{uuid.uuid4().hex[:8]}"
        now_str = datetime.now(timezone.utc).isoformat()

        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO remediation_records (
                    remediation_id, student_id, concept_id, prerequisite_concept_id,
                    gap_summary, ncert_reference, explanation, example_activity,
                    practice_question_id, is_completed, mastery_before, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?);
                """,
                (rem_id, student_id, concept_id, prereq_id, gap_summary, ncert_ref, explanation, example, question_id, mastery_before, now_str)
            )
            conn.commit()
            return rem_id

    def complete_remediation_event(
        self,
        remediation_id: str,
        student_answer: str,
        mastery_after: float
    ) -> bool:
        now_str = datetime.now(timezone.utc).isoformat()
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                UPDATE remediation_records
                SET student_answer = ?, is_completed = 1, mastery_after = ?, completed_at = ?
                WHERE remediation_id = ?;
                """,
                (student_answer, mastery_after, now_str, remediation_id)
            )
            conn.commit()
            return cur.rowcount > 0

    # --------------------------------------------------------------------------
    # 4. Curriculum Embeddings Persistence (RAG)
    # --------------------------------------------------------------------------
    def store_embedding_chunk(
        self,
        chunk_id: str,
        chapter_id: str,
        topic_id: Optional[str],
        concept_id: Optional[str],
        source_doc_id: Optional[str],
        page_num: Optional[int],
        heading: Optional[str],
        chunk_text: str,
        metadata: Optional[Dict[str, Any]] = None
    ):
        meta_json = json.dumps(metadata or {})
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO curriculum_embeddings (
                    chunk_id, chapter_id, topic_id, concept_id, source_doc_id,
                    page_number, section_heading, chunk_text, metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(chunk_id) DO UPDATE SET
                    chunk_text = excluded.chunk_text,
                    metadata_json = excluded.metadata_json;
                """,
                (chunk_id, chapter_id, topic_id, concept_id, source_doc_id, page_num, heading, chunk_text, meta_json)
            )
            conn.commit()

    def get_chunks_by_chapter(self, chapter_id: str = "CH-01") -> List[Dict[str, Any]]:
        norm_id = chapter_id if "-" in chapter_id else f"{chapter_id[:2]}-{chapter_id[2:]}"
        alt_id = chapter_id.replace("-", "")
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT * FROM curriculum_embeddings
                WHERE chapter_id IN (?, ?)
                ORDER BY page_number ASC;
                """,
                (norm_id, alt_id)
            )
            rows = cur.fetchall()
            return [dict(r) for r in rows]
