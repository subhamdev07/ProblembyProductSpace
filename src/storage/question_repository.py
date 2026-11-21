"""
Question Repository Layer
Provides transactional SQLite storage and retrieval for Questions,
Question-Concept junction mappings, and Question-Learning Outcome mappings.
"""

import json
from typing import List, Dict, Any, Optional
from src.storage.database import Database
from src.models.question import (
    Question,
    QuestionType,
    QuestionDifficulty,
    CognitiveLevel,
    QuestionStatus,
    QuestionProvenance,
)
from src.models.concept import ConceptVerificationStatus, SourceStatus


class QuestionRepository:
    """
    CRUD and query operations for Question entities.
    """

    def __init__(self, db: Database):
        self.db = db

    def upsert_question(self, question: Question) -> None:
        """
        Inserts or updates a question, maintaining concept and LO junction mappings in a transaction.
        """
        sql_question = """
        INSERT INTO questions (
            question_id, question_text, question_type, chapter_id, topic_id,
            difficulty, cognitive_level, marks, expected_time_seconds,
            answer_key_json, explanation, misconception_tags_json,
            source_status, verification_status, question_status,
            provenance_json, updated_at
        ) VALUES (
            :question_id, :question_text, :question_type, :chapter_id, :topic_id,
            :difficulty, :cognitive_level, :marks, :expected_time_seconds,
            :answer_key_json, :explanation, :misconception_tags_json,
            :source_status, :verification_status, :question_status,
            :provenance_json, CURRENT_TIMESTAMP
        ) ON CONFLICT(question_id) DO UPDATE SET
            question_text = excluded.question_text,
            question_type = excluded.question_type,
            chapter_id = excluded.chapter_id,
            topic_id = excluded.topic_id,
            difficulty = excluded.difficulty,
            cognitive_level = excluded.cognitive_level,
            marks = excluded.marks,
            expected_time_seconds = excluded.expected_time_seconds,
            answer_key_json = excluded.answer_key_json,
            explanation = excluded.explanation,
            misconception_tags_json = excluded.misconception_tags_json,
            source_status = excluded.source_status,
            verification_status = excluded.verification_status,
            question_status = excluded.question_status,
            provenance_json = excluded.provenance_json,
            updated_at = CURRENT_TIMESTAMP;
        """

        params = {
            "question_id": question.question_id,
            "question_text": question.question_text,
            "question_type": question.question_type.value if hasattr(question.question_type, "value") else str(question.question_type),
            "chapter_id": question.chapter_id,
            "topic_id": question.topic_id,
            "difficulty": question.difficulty.value if hasattr(question.difficulty, "value") else str(question.difficulty),
            "cognitive_level": question.cognitive_level.value if hasattr(question.cognitive_level, "value") else str(question.cognitive_level),
            "marks": question.marks,
            "expected_time_seconds": question.expected_time_seconds,
            "answer_key_json": json.dumps(question.answer_key or {}),
            "explanation": question.explanation,
            "misconception_tags_json": json.dumps(question.misconception_tags or []),
            "source_status": question.source_status.value if hasattr(question.source_status, "value") else str(question.source_status),
            "verification_status": question.verification_status.value if hasattr(question.verification_status, "value") else str(question.verification_status),
            "question_status": question.question_status.value if hasattr(question.question_status, "value") else str(question.question_status),
            "provenance_json": json.dumps(question.provenance.model_dump() if question.provenance else {}),
        }

        with self.db.get_connection() as conn:
            conn.execute(sql_question, params)

            # Refresh concept mappings
            conn.execute("DELETE FROM question_concept_mappings WHERE question_id = ?;", (question.question_id,))
            for idx, cid in enumerate(question.concept_ids):
                mapping_id = f"QCM-{question.question_id}-{cid}"
                is_pri = 1 if idx == 0 else 0
                conn.execute(
                    """
                    INSERT INTO question_concept_mappings (mapping_id, question_id, concept_id, is_primary)
                    VALUES (?, ?, ?, ?);
                    """,
                    (mapping_id, question.question_id, cid, is_pri),
                )

            # Refresh learning outcome mappings
            conn.execute("DELETE FROM question_learning_outcome_mappings WHERE question_id = ?;", (question.question_id,))
            for loid in question.learning_outcome_ids:
                mapping_id = f"QLO-{question.question_id}-{loid}"
                conn.execute(
                    """
                    INSERT INTO question_learning_outcome_mappings (mapping_id, question_id, outcome_id)
                    VALUES (?, ?, ?);
                    """,
                    (mapping_id, question.question_id, loid),
                )

    def get_question(self, question_id: str) -> Optional[Question]:
        """
        Retrieves a question by ID along with its mapped concepts and learning outcomes.
        """
        sql = "SELECT * FROM questions WHERE question_id = ?;"
        with self.db.get_connection() as conn:
            row = conn.execute(sql, (question_id,)).fetchone()
            if not row:
                return None
            return self._row_to_question(row, conn)

    def delete_question(self, question_id: str) -> bool:
        """
        Deletes a question by ID. Cascades to junction tables.
        Returns True if a record was deleted, False otherwise.
        """
        sql = "DELETE FROM questions WHERE question_id = ?;"
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(sql, (question_id,))
            conn.commit()
            return cur.rowcount > 0

    def get_questions_by_chapter(self, chapter_id: str) -> List[Question]:
        """
        Retrieves all questions belonging to a chapter.
        """
        sql = "SELECT * FROM questions WHERE chapter_id = ? ORDER BY question_id;"
        with self.db.get_connection() as conn:
            rows = conn.execute(sql, (chapter_id,)).fetchall()
            return [self._row_to_question(r, conn) for r in rows]

    def get_questions_by_topic(self, topic_id: str) -> List[Question]:
        """
        Retrieves all questions belonging to a topic.
        """
        sql = "SELECT * FROM questions WHERE topic_id = ? ORDER BY question_id;"
        with self.db.get_connection() as conn:
            rows = conn.execute(sql, (topic_id,)).fetchall()
            return [self._row_to_question(r, conn) for r in rows]

    def get_questions_by_concept(self, concept_id: str) -> List[Question]:
        """
        Retrieves all questions linked to a given concept node.
        """
        sql = """
        SELECT q.* FROM questions q
        JOIN question_concept_mappings m ON q.question_id = m.question_id
        WHERE m.concept_id = ?
        ORDER BY q.question_id;
        """
        with self.db.get_connection() as conn:
            rows = conn.execute(sql, (concept_id,)).fetchall()
            return [self._row_to_question(r, conn) for r in rows]

    def filter_questions(
        self,
        chapter_id: Optional[str] = None,
        topic_id: Optional[str] = None,
        concept_id: Optional[str] = None,
        difficulty: Optional[Union[QuestionDifficulty, str]] = None,
        cognitive_level: Optional[Union[CognitiveLevel, str]] = None,
        question_type: Optional[Union[QuestionType, str]] = None,
        question_status: Optional[Union[QuestionStatus, str]] = None,
    ) -> List[Question]:
        """
        Flexible filter query supporting chapter, topic, concept, difficulty,
        cognitive level, question type, and status.
        """
        clauses = []
        params = []

        if chapter_id:
            clauses.append("q.chapter_id = ?")
            params.append(chapter_id)
        if topic_id:
            clauses.append("q.topic_id = ?")
            params.append(topic_id)
        if difficulty:
            diff_val = difficulty.value if hasattr(difficulty, "value") else str(difficulty)
            clauses.append("q.difficulty = ?")
            params.append(diff_val)
        if cognitive_level:
            cog_val = cognitive_level.value if hasattr(cognitive_level, "value") else str(cognitive_level)
            clauses.append("q.cognitive_level = ?")
            params.append(cog_val)
        if question_type:
            qtype_val = question_type.value if hasattr(question_type, "value") else str(question_type)
            clauses.append("q.question_type = ?")
            params.append(qtype_val)
        if question_status:
            stat_val = question_status.value if hasattr(question_status, "value") else str(question_status)
            clauses.append("q.question_status = ?")
            params.append(stat_val)

        if concept_id:
            sql = """
            SELECT DISTINCT q.* FROM questions q
            JOIN question_concept_mappings m ON q.question_id = m.question_id
            WHERE m.concept_id = ?
            """
            params = [concept_id] + params
            if clauses:
                sql += " AND " + " AND ".join(clauses)
            sql += " ORDER BY q.question_id;"
        else:
            sql = "SELECT q.* FROM questions q"
            if clauses:
                sql += " WHERE " + " AND ".join(clauses)
            sql += " ORDER BY q.question_id;"

        with self.db.get_connection() as conn:
            rows = conn.execute(sql, params).fetchall()
            return [self._row_to_question(r, conn) for r in rows]

    def get_all_questions(self) -> List[Question]:
        """
        Retrieves all questions in the database.
        """
        sql = "SELECT * FROM questions ORDER BY chapter_id, question_id;"
        with self.db.get_connection() as conn:
            rows = conn.execute(sql).fetchall()
            return [self._row_to_question(r, conn) for r in rows]

    def _row_to_question(self, row: Any, conn: Any) -> Question:
        qid = row["question_id"]
        # Fetch concept mappings
        cur = conn.cursor()
        cur.execute("SELECT concept_id FROM question_concept_mappings WHERE question_id = ? ORDER BY is_primary DESC, concept_id;", (qid,))
        concept_ids = [r[0] for r in cur.fetchall()]

        # Fetch learning outcome mappings
        cur.execute("SELECT outcome_id FROM question_learning_outcome_mappings WHERE question_id = ? ORDER BY outcome_id;", (qid,))
        outcome_ids = [r[0] for r in cur.fetchall()]

        answer_key = {}
        if row["answer_key_json"]:
            try:
                answer_key = json.loads(row["answer_key_json"])
            except Exception:
                pass

        misconception_tags = []
        if row["misconception_tags_json"]:
            try:
                misconception_tags = json.loads(row["misconception_tags_json"])
            except Exception:
                pass

        prov = None
        if row["provenance_json"]:
            try:
                pdata = json.loads(row["provenance_json"])
                if pdata and "source_document_id" in pdata:
                    prov = QuestionProvenance(**pdata)
            except Exception:
                pass

        return Question(
            question_id=row["question_id"],
            question_text=row["question_text"],
            question_type=QuestionType(row["question_type"]),
            chapter_id=row["chapter_id"],
            topic_id=row["topic_id"],
            concept_ids=concept_ids,
            learning_outcome_ids=outcome_ids,
            difficulty=QuestionDifficulty(row["difficulty"]),
            cognitive_level=CognitiveLevel(row["cognitive_level"]),
            marks=row["marks"],
            expected_time_seconds=row["expected_time_seconds"],
            answer_key=answer_key,
            explanation=row["explanation"],
            misconception_tags=misconception_tags,
            source_status=SourceStatus(row["source_status"]),
            verification_status=ConceptVerificationStatus(row["verification_status"]),
            question_status=QuestionStatus(row["question_status"]),
            provenance=prov,
            created_at=str(row["created_at"]) if row["created_at"] else None,
            updated_at=str(row["updated_at"]) if row["updated_at"] else None,
        )

    def get_question_statistics(self) -> Dict[str, Any]:
        """
        Aggregates question bank metrics across multiple dimensions.
        """
        with self.db.get_connection() as conn:
            total_questions = conn.execute("SELECT COUNT(*) FROM questions;").fetchone()[0]

            by_difficulty = {}
            for r in conn.execute("SELECT difficulty, COUNT(*) FROM questions GROUP BY difficulty;").fetchall():
                by_difficulty[r[0]] = r[1]

            by_cognitive = {}
            for r in conn.execute("SELECT cognitive_level, COUNT(*) FROM questions GROUP BY cognitive_level;").fetchall():
                by_cognitive[r[0]] = r[1]

            by_type = {}
            for r in conn.execute("SELECT question_type, COUNT(*) FROM questions GROUP BY question_type;").fetchall():
                by_type[r[0]] = r[1]

            by_status = {}
            for r in conn.execute("SELECT question_status, COUNT(*) FROM questions GROUP BY question_status;").fetchall():
                by_status[r[0]] = r[1]

            by_chapter = {}
            for r in conn.execute("SELECT chapter_id, COUNT(*) FROM questions GROUP BY chapter_id;").fetchall():
                by_chapter[r[0]] = r[1]

            total_concepts_mapped = conn.execute("SELECT COUNT(DISTINCT concept_id) FROM question_concept_mappings;").fetchone()[0]

            return {
                "total_questions": total_questions,
                "by_difficulty": by_difficulty,
                "by_cognitive_level": by_cognitive,
                "by_question_type": by_type,
                "by_question_status": by_status,
                "by_chapter": by_chapter,
                "distinct_concepts_covered": total_concepts_mapped,
            }
