"""
Examination Repository Layer (P5)
Provides transactional SQLite storage and retrieval for Examination Blueprints,
Pre-generated Templates, Live Examination Sessions, Student Answers, and Result Summaries.
"""

import json
import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional

from src.storage.database import Database
from src.models.examination import (
    ExaminationStatus,
    ExamSectionConfig,
    ExaminationBlueprint,
    ExaminationQuestionItem,
    ExaminationSessionState,
    SaveExamAnswerResponse,
    ExaminationOverviewItem,
)
from src.models.question import QuestionType, QuestionDifficulty, CognitiveLevel


class ExaminationRepository:
    def __init__(self, db: Database):
        self.db = db

    # --------------------------------------------------------------------------
    # 1. Blueprints
    # --------------------------------------------------------------------------
    def upsert_blueprint(self, bp: ExaminationBlueprint) -> None:
        sql = """
        INSERT INTO examination_blueprints (
            blueprint_id, title, curriculum_id, academic_session,
            total_marks, duration_minutes, question_count,
            sections_config_json, unit_weightage_json, cognitive_distribution_json,
            instructions_json, is_official
        ) VALUES (
            :blueprint_id, :title, :curriculum_id, :academic_session,
            :total_marks, :duration_minutes, :question_count,
            :sections_config_json, :unit_weightage_json, :cognitive_distribution_json,
            :instructions_json, :is_official
        ) ON CONFLICT(blueprint_id) DO UPDATE SET
            title = excluded.title,
            total_marks = excluded.total_marks,
            duration_minutes = excluded.duration_minutes,
            question_count = excluded.question_count,
            sections_config_json = excluded.sections_config_json,
            unit_weightage_json = excluded.unit_weightage_json,
            cognitive_distribution_json = excluded.cognitive_distribution_json,
            instructions_json = excluded.instructions_json,
            is_official = excluded.is_official;
        """
        params = {
            "blueprint_id": bp.blueprint_id,
            "title": bp.title,
            "curriculum_id": bp.curriculum_id,
            "academic_session": bp.academic_session,
            "total_marks": bp.total_marks,
            "duration_minutes": bp.duration_minutes,
            "question_count": bp.question_count,
            "sections_config_json": json.dumps([s.model_dump() for s in bp.sections]),
            "unit_weightage_json": json.dumps(bp.unit_weightage),
            "cognitive_distribution_json": json.dumps(bp.cognitive_distribution),
            "instructions_json": json.dumps(bp.general_instructions),
            "is_official": 1 if bp.is_official else 0,
        }
        with self.db.get_connection() as conn:
            conn.execute(sql, params)
            conn.commit()

    def get_blueprint(self, blueprint_id: str) -> Optional[ExaminationBlueprint]:
        with self.db.get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM examination_blueprints WHERE blueprint_id = ?;", (blueprint_id,)
            ).fetchone()
            if not row:
                return None
            return self._row_to_blueprint(row)

    def get_all_blueprints(self) -> List[ExaminationBlueprint]:
        with self.db.get_connection() as conn:
            rows = conn.execute("SELECT * FROM examination_blueprints ORDER BY blueprint_id;").fetchall()
            return [self._row_to_blueprint(r) for r in rows]

    def _row_to_blueprint(self, row: Any) -> ExaminationBlueprint:
        sections_raw = json.loads(row["sections_config_json"]) if row["sections_config_json"] else []
        sections = [ExamSectionConfig(**s) for s in sections_raw]
        return ExaminationBlueprint(
            blueprint_id=row["blueprint_id"],
            title=row["title"],
            academic_session=row["academic_session"],
            curriculum_id=row["curriculum_id"],
            total_marks=row["total_marks"],
            duration_minutes=row["duration_minutes"],
            question_count=row["question_count"],
            sections=sections,
            unit_weightage=json.loads(row["unit_weightage_json"]) if row["unit_weightage_json"] else {},
            cognitive_distribution=json.loads(row["cognitive_distribution_json"]) if row["cognitive_distribution_json"] else {},
            general_instructions=json.loads(row["instructions_json"]) if row["instructions_json"] else [],
            is_official=bool(row["is_official"]),
        )

    # --------------------------------------------------------------------------
    # 2. Templates
    # --------------------------------------------------------------------------
    def upsert_template(
        self,
        template_id: str,
        blueprint_id: str,
        paper_code: str,
        title: str,
        question_ids: List[str],
        total_marks: int
    ) -> None:
        sql = """
        INSERT INTO examination_templates (
            template_id, blueprint_id, paper_code, title, questions_sequence_json, total_marks
        ) VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(template_id) DO UPDATE SET
            paper_code = excluded.paper_code,
            title = excluded.title,
            questions_sequence_json = excluded.questions_sequence_json,
            total_marks = excluded.total_marks;
        """
        with self.db.get_connection() as conn:
            conn.execute(sql, (template_id, blueprint_id, paper_code, title, json.dumps(question_ids), total_marks))
            conn.commit()

    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT * FROM examination_templates WHERE template_id = ?;", (template_id,)).fetchone()
            return dict(row) if row else None

    def get_template_by_code(self, paper_code: str) -> Optional[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT * FROM examination_templates WHERE paper_code = ?;", (paper_code,)).fetchone()
            return dict(row) if row else None

    # --------------------------------------------------------------------------
    # 3. Examination Sessions
    # --------------------------------------------------------------------------
    def create_session(
        self,
        session_id: str,
        student_id: str,
        blueprint_id: str,
        template_id: Optional[str],
        paper_title: str,
        duration_minutes: int,
        total_marks: int,
        total_questions: int,
    ) -> Dict[str, Any]:
        started_at_dt = datetime.now(timezone.utc)
        expires_at_dt = started_at_dt + timedelta(minutes=duration_minutes)

        sql = """
        INSERT INTO examination_sessions (
            session_id, student_id, blueprint_id, template_id, paper_title,
            status, started_at, expires_at, total_marks, total_questions, duration_minutes
        ) VALUES (?, ?, ?, ?, ?, 'IN_PROGRESS', ?, ?, ?, ?, ?);
        """
        with self.db.get_connection() as conn:
            conn.execute(
                sql,
                (
                    session_id,
                    student_id,
                    blueprint_id,
                    template_id,
                    paper_title,
                    started_at_dt.isoformat(),
                    expires_at_dt.isoformat(),
                    total_marks,
                    total_questions,
                    duration_minutes,
                ),
            )
            conn.commit()

        return {
            "session_id": session_id,
            "student_id": student_id,
            "blueprint_id": blueprint_id,
            "template_id": template_id,
            "paper_title": paper_title,
            "status": "IN_PROGRESS",
            "started_at": started_at_dt.isoformat(),
            "expires_at": expires_at_dt.isoformat(),
            "total_marks": total_marks,
            "total_questions": total_questions,
            "duration_minutes": duration_minutes,
        }

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT * FROM examination_sessions WHERE session_id = ?;", (session_id,)).fetchone()
            return dict(row) if row else None

    def get_active_session_for_student(self, student_id: str) -> Optional[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            row = conn.execute(
                """
                SELECT * FROM examination_sessions
                WHERE student_id = ? AND status = 'IN_PROGRESS'
                ORDER BY started_at DESC LIMIT 1;
                """,
                (student_id,),
            ).fetchone()
            return dict(row) if row else None

    def get_student_sessions(self, student_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            rows = conn.execute(
                """
                SELECT * FROM examination_sessions
                WHERE student_id = ?
                ORDER BY started_at DESC LIMIT ?;
                """,
                (student_id, limit),
            ).fetchall()
            return [dict(r) for r in rows]

    def update_session_completion(
        self,
        session_id: str,
        status: ExaminationStatus,
        score: float,
        percentage: float,
        time_spent_seconds: int,
        is_timeout: bool = False,
    ) -> None:
        sql = """
        UPDATE examination_sessions
        SET status = ?,
            score = ?,
            percentage = ?,
            time_spent_seconds = ?,
            is_timeout_submission = ?,
            submitted_at = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE session_id = ?;
        """
        now_iso = datetime.now(timezone.utc).isoformat()
        with self.db.get_connection() as conn:
            conn.execute(
                sql,
                (
                    status.value if hasattr(status, "value") else str(status),
                    score,
                    percentage,
                    time_spent_seconds,
                    1 if is_timeout else 0,
                    now_iso,
                    session_id,
                ),
            )
            conn.commit()

    # --------------------------------------------------------------------------
    # 4. Examination Answers (Real-time Persistence)
    # --------------------------------------------------------------------------
    def save_or_update_answer(
        self,
        session_id: str,
        student_id: str,
        question_id: str,
        question_number: int,
        section_name: str,
        submitted_answer: Dict[str, Any],
        is_marked_for_review: bool = False,
        time_spent_seconds: int = 0,
    ) -> Dict[str, Any]:
        ans_id = str(uuid.uuid4())
        is_answered = 1 if submitted_answer else 0
        ans_json = json.dumps(submitted_answer)

        sql = """
        INSERT INTO examination_answers (
            answer_id, session_id, student_id, question_id, question_number,
            section_name, submitted_answer_json, is_marked_for_review,
            is_answered, time_spent_seconds, last_saved_at
        ) VALUES (
            :answer_id, :session_id, :student_id, :question_id, :question_number,
            :section_name, :submitted_answer_json, :is_marked_for_review,
            :is_answered, :time_spent_seconds, CURRENT_TIMESTAMP
        ) ON CONFLICT(session_id, question_id) DO UPDATE SET
            submitted_answer_json = excluded.submitted_answer_json,
            is_marked_for_review = excluded.is_marked_for_review,
            is_answered = excluded.is_answered,
            time_spent_seconds = examination_answers.time_spent_seconds + excluded.time_spent_seconds,
            last_saved_at = CURRENT_TIMESTAMP;
        """
        params = {
            "answer_id": ans_id,
            "session_id": session_id,
            "student_id": student_id,
            "question_id": question_id,
            "question_number": question_number,
            "section_name": section_name,
            "submitted_answer_json": ans_json,
            "is_marked_for_review": 1 if is_marked_for_review else 0,
            "is_answered": is_answered,
            "time_spent_seconds": time_spent_seconds,
        }
        with self.db.get_connection() as conn:
            conn.execute(sql, params)
            conn.commit()

        return self.get_session_answer_counts(session_id)

    def get_session_answers(self, session_id: str) -> List[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            rows = conn.execute(
                """
                SELECT * FROM examination_answers
                WHERE session_id = ?
                ORDER BY question_number ASC;
                """,
                (session_id,),
            ).fetchall()
            results = []
            for r in rows:
                item = dict(r)
                if item["submitted_answer_json"]:
                    try:
                        item["submitted_answer"] = json.loads(item["submitted_answer_json"])
                    except Exception:
                        item["submitted_answer"] = item["submitted_answer_json"]
                else:
                    item["submitted_answer"] = None
                results.append(item)
            return results

    def get_session_answer_counts(self, session_id: str) -> Dict[str, int]:
        with self.db.get_connection() as conn:
            row = conn.execute(
                """
                SELECT 
                    COUNT(*) as total_recorded,
                    SUM(CASE WHEN is_answered = 1 THEN 1 ELSE 0 END) as answered,
                    SUM(CASE WHEN is_marked_for_review = 1 THEN 1 ELSE 0 END) as marked
                FROM examination_answers
                WHERE session_id = ?;
                """,
                (session_id,),
            ).fetchone()

            answered = row["answered"] or 0
            marked = row["marked"] or 0
            return {
                "answered": answered,
                "marked": marked,
            }

    def record_evaluated_answer(
        self,
        session_id: str,
        question_id: str,
        is_correct: bool,
        marks_awarded: float,
        feedback: str,
    ) -> None:
        sql = """
        UPDATE examination_answers
        SET is_correct = ?,
            marks_awarded = ?,
            evaluation_feedback = ?
        WHERE session_id = ? AND question_id = ?;
        """
        with self.db.get_connection() as conn:
            conn.execute(sql, (1 if is_correct else 0, marks_awarded, feedback, session_id, question_id))
            conn.commit()

    # --------------------------------------------------------------------------
    # 5. Examination Results
    # --------------------------------------------------------------------------
    def store_result(
        self,
        session_id: str,
        student_id: str,
        total_marks: int,
        score: float,
        percentage: float,
        section_scores: Dict[str, Any],
        unit_scores: Dict[str, Any],
        chapter_scores: Dict[str, Any],
        difficulty_scores: Dict[str, Any],
        cognitive_scores: Dict[str, Any],
        strong_concepts: List[Dict[str, Any]],
        weak_concepts: List[Dict[str, Any]],
        misconceptions: List[str],
        recommended_remediation: Dict[str, Any],
    ) -> str:
        result_id = str(uuid.uuid4())
        sql = """
        INSERT INTO examination_results (
            result_id, session_id, student_id, total_marks, score_obtained, percentage,
            section_scores_json, unit_scores_json, chapter_scores_json, difficulty_scores_json,
            cognitive_scores_json, weak_concepts_json, strong_concepts_json,
            misconceptions_detected_json, recommended_remediation_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(session_id) DO UPDATE SET
            score_obtained = excluded.score_obtained,
            percentage = excluded.percentage,
            section_scores_json = excluded.section_scores_json,
            unit_scores_json = excluded.unit_scores_json,
            chapter_scores_json = excluded.chapter_scores_json,
            difficulty_scores_json = excluded.difficulty_scores_json,
            cognitive_scores_json = excluded.cognitive_scores_json,
            weak_concepts_json = excluded.weak_concepts_json,
            strong_concepts_json = excluded.strong_concepts_json,
            misconceptions_detected_json = excluded.misconceptions_detected_json,
            recommended_remediation_json = excluded.recommended_remediation_json,
            completed_at = CURRENT_TIMESTAMP;
        """
        with self.db.get_connection() as conn:
            conn.execute(
                sql,
                (
                    result_id,
                    session_id,
                    student_id,
                    total_marks,
                    score,
                    percentage,
                    json.dumps(section_scores),
                    json.dumps(unit_scores),
                    json.dumps(chapter_scores),
                    json.dumps(difficulty_scores),
                    json.dumps(cognitive_scores),
                    json.dumps(weak_concepts),
                    json.dumps(strong_concepts),
                    json.dumps(misconceptions),
                    json.dumps(recommended_remediation),
                ),
            )
            conn.commit()
        return result_id

    def get_result_by_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT * FROM examination_results WHERE session_id = ?;", (session_id,)).fetchone()
            if not row:
                return None
            res = dict(row)
            res["section_scores"] = json.loads(res["section_scores_json"])
            res["unit_scores"] = json.loads(res["unit_scores_json"])
            res["chapter_scores"] = json.loads(res["chapter_scores_json"])
            res["difficulty_scores"] = json.loads(res["difficulty_scores_json"])
            res["cognitive_scores"] = json.loads(res["cognitive_scores_json"])
            res["weak_concepts"] = json.loads(res["weak_concepts_json"])
            res["strong_concepts"] = json.loads(res["strong_concepts_json"])
            res["misconceptions_detected"] = json.loads(res["misconceptions_detected_json"])
            res["recommended_remediation"] = json.loads(res["recommended_remediation_json"])
            return res

    def get_all_results(self) -> List[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            rows = conn.execute(
                """
                SELECT r.*, s.name as student_name, e.paper_title, e.duration_minutes
                FROM examination_results r
                JOIN students s ON r.student_id = s.student_id
                JOIN examination_sessions e ON r.session_id = e.session_id
                ORDER BY r.completed_at DESC;
                """
            ).fetchall()
            return [dict(r) for r in rows]
