"""
Database Connection and Repository Layer
Provides transactional SQLite management with strict foreign key enforcement.
"""

import os
import sqlite3
import json
import gc
from typing import List, Dict, Any, Optional
from pathlib import Path


class Database:
    """
    SQLite Database Manager with Foreign Key enforcement and migration support.
    """

    def __init__(self, db_path: Optional[str] = None):
        if db_path is None or db_path == "data/curriculum.db":
            if os.environ.get("VERCEL") or os.environ.get("AWS_LAMBDA_FUNCTION_NAME"):
                tmp_dir = "/tmp"
                tmp_db = os.path.join(tmp_dir, "curriculum.db")
                source_db = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "data", "curriculum.db")
                if not os.path.exists(tmp_db) and os.path.exists(source_db):
                    import shutil
                    shutil.copy2(source_db, tmp_db)
                self.db_path = tmp_db
            else:
                self.db_path = "data/curriculum.db"
        else:
            self.db_path = db_path
        if os.path.dirname(os.path.abspath(self.db_path)):
            try:
                os.makedirs(os.path.dirname(os.path.abspath(self.db_path)), exist_ok=True)
            except Exception:
                pass
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON;")
        return conn

    def init_db(self):
        schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
        with open(schema_path, "r", encoding="utf-8") as f:
            schema_sql = f.read()

        try:
            with self.get_connection() as conn:
                conn.executescript(schema_sql)
                try:
                    conn.execute("ALTER TABLE student_misconceptions ADD COLUMN evidence_text TEXT;")
                except sqlite3.OperationalError:
                    pass
        except Exception:
            pass

    def reset_db(self):
        """Drops all tables and recreates them cleanly."""
        with self.get_connection() as conn:
            conn.execute("PRAGMA foreign_keys = OFF;")
            tables = [
                "curriculum_embeddings",
                "remediation_records",
                "spaced_repetition_schedules",
                "student_misconceptions",
                "learner_concept_mastery",
                "student_answers",
                "assessment_questions",
                "assessments",
                "students",
                "question_learning_outcome_mappings",
                "question_concept_mappings",
                "questions",
                "concept_provenance",
                "concept_relationships",
                "concepts",
                "source_citations",
                "curriculum_mappings",
                "learning_outcomes",
                "subtopics",
                "topics",
                "chapters",
                "units",
                "curricula",
                "subjects",
                "academic_sessions",
                "source_documents",
            ]
            for t in tables:
                conn.execute(f"DROP TABLE IF EXISTS {t};")
            conn.execute("PRAGMA foreign_keys = ON;")
        self.init_db()


class CurriculumRepository:
    """
    CRUD and query operations for curriculum entities.
    """

    def __init__(self, db: Database):
        self.db = db

    # Source Documents
    def upsert_source_document(self, doc_dict: Dict[str, Any]):
        sql = """
        INSERT INTO source_documents (
            document_id, title, document_type, academic_session, subject,
            subject_code, source_authority, file_path, file_size_bytes,
            sha256_hash, page_count, verification_status, metadata_json
        ) VALUES (
            :document_id, :title, :document_type, :academic_session, :subject,
            :subject_code, :source_authority, :file_path, :file_size_bytes,
            :sha256_hash, :page_count, :verification_status, :metadata_json
        ) ON CONFLICT(document_id) DO UPDATE SET
            title=excluded.title,
            document_type=excluded.document_type,
            academic_session=excluded.academic_session,
            subject=excluded.subject,
            subject_code=excluded.subject_code,
            source_authority=excluded.source_authority,
            file_path=excluded.file_path,
            file_size_bytes=excluded.file_size_bytes,
            sha256_hash=excluded.sha256_hash,
            page_count=excluded.page_count,
            verification_status=excluded.verification_status,
            metadata_json=excluded.metadata_json;
        """
        params = dict(doc_dict)
        params.setdefault("subject_code", None)
        params.setdefault("file_path", None)
        params.setdefault("file_size_bytes", None)
        params.setdefault("sha256_hash", None)
        params.setdefault("page_count", None)
        meta = params.get("metadata_json") or params.get("metadata", {})
        params["metadata_json"] = json.dumps(meta) if isinstance(meta, (dict, list)) else str(meta or "{}")

        with self.db.get_connection() as conn:
            conn.execute(sql, params)

    def get_source_documents(self) -> List[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM source_documents ORDER BY document_id")
            return [dict(row) for row in cursor.fetchall()]

    # Academic Session
    def upsert_academic_session(self, session_dict: Dict[str, Any]):
        sql = """
        INSERT INTO academic_sessions (session_id, name, start_year, end_year, is_active)
        VALUES (:session_id, :name, :start_year, :end_year, :is_active)
        ON CONFLICT(session_id) DO UPDATE SET
            name=excluded.name,
            start_year=excluded.start_year,
            end_year=excluded.end_year,
            is_active=excluded.is_active;
        """
        params = dict(session_dict)
        params.setdefault("is_active", 1)
        with self.db.get_connection() as conn:
            conn.execute(sql, params)

    # Subject
    def upsert_subject(self, subj_dict: Dict[str, Any]):
        sql = """
        INSERT INTO subjects (subject_id, code, name, class_level, description)
        VALUES (:subject_id, :code, :name, :class_level, :description)
        ON CONFLICT(subject_id) DO UPDATE SET
            code=excluded.code,
            name=excluded.name,
            class_level=excluded.class_level,
            description=excluded.description;
        """
        params = dict(subj_dict)
        params.setdefault("class_level", 10)
        params.setdefault("description", None)
        with self.db.get_connection() as conn:
            conn.execute(sql, params)

    # Curriculum
    def upsert_curriculum(self, curr_dict: Dict[str, Any]):
        sql = """
        INSERT INTO curricula (curriculum_id, name, session_id, subject_id, class_level, authority, metadata_json)
        VALUES (:curriculum_id, :name, :session_id, :subject_id, :class_level, :authority, :metadata_json)
        ON CONFLICT(curriculum_id) DO UPDATE SET
            name=excluded.name,
            session_id=excluded.session_id,
            subject_id=excluded.subject_id,
            class_level=excluded.class_level,
            authority=excluded.authority,
            metadata_json=excluded.metadata_json;
        """
        params = dict(curr_dict)
        params.setdefault("class_level", 10)
        params.setdefault("authority", "CBSE")
        meta = params.get("metadata_json") or params.get("metadata", {})
        params["metadata_json"] = json.dumps(meta) if isinstance(meta, (dict, list)) else str(meta or "{}")

        with self.db.get_connection() as conn:
            conn.execute(sql, params)

    # Units
    def upsert_unit(self, unit_dict: Dict[str, Any]):
        sql = """
        INSERT INTO units (
            unit_id, unit_number, name, theme, curriculum_id, marks,
            verification_status, source_doc_id, source_page, source_section
        ) VALUES (
            :unit_id, :unit_number, :name, :theme, :curriculum_id, :marks,
            :verification_status, :source_doc_id, :source_page, :source_section
        ) ON CONFLICT(unit_id) DO UPDATE SET
            unit_number=excluded.unit_number,
            name=excluded.name,
            theme=excluded.theme,
            curriculum_id=excluded.curriculum_id,
            marks=excluded.marks,
            verification_status=excluded.verification_status,
            source_doc_id=excluded.source_doc_id,
            source_page=excluded.source_page,
            source_section=excluded.source_section;
        """
        params = dict(unit_dict)
        params.setdefault("theme", None)
        params.setdefault("marks", None)
        params.setdefault("source_doc_id", None)
        params.setdefault("source_page", None)
        params.setdefault("source_section", None)

        with self.db.get_connection() as conn:
            conn.execute(sql, params)

    def get_units(self) -> List[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM units ORDER BY unit_number")
            return [dict(row) for row in cursor.fetchall()]

    # Chapters
    def upsert_chapter(self, ch_dict: Dict[str, Any]):
        sql = """
        INSERT INTO chapters (
            chapter_id, chapter_number, name, unit_id, curriculum_id,
            assessment_status, verification_status, metadata_json
        ) VALUES (
            :chapter_id, :chapter_number, :name, :unit_id, :curriculum_id,
            :assessment_status, :verification_status, :metadata_json
        ) ON CONFLICT(chapter_id) DO UPDATE SET
            chapter_number=excluded.chapter_number,
            name=excluded.name,
            unit_id=excluded.unit_id,
            curriculum_id=excluded.curriculum_id,
            assessment_status=excluded.assessment_status,
            verification_status=excluded.verification_status,
            metadata_json=excluded.metadata_json;
        """
        params = dict(ch_dict)
        meta = params.get("metadata_json") or params.get("metadata", {})
        params["metadata_json"] = json.dumps(meta) if isinstance(meta, (dict, list)) else str(meta or "{}")

        with self.db.get_connection() as conn:
            conn.execute(sql, params)

    def get_chapters(self) -> List[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM chapters ORDER BY chapter_number")
            return [dict(row) for row in cursor.fetchall()]

    # Topics
    def upsert_topic(self, topic_dict: Dict[str, Any]):
        sql = """
        INSERT INTO topics (
            topic_id, chapter_id, name, sequence_order, description,
            assessment_status, verification_status, source_doc_id,
            source_page_start, source_page_end, source_section, metadata_json
        ) VALUES (
            :topic_id, :chapter_id, :name, :sequence_order, :description,
            :assessment_status, :verification_status, :source_doc_id,
            :source_page_start, :source_page_end, :source_section, :metadata_json
        ) ON CONFLICT(topic_id) DO UPDATE SET
            chapter_id=excluded.chapter_id,
            name=excluded.name,
            sequence_order=excluded.sequence_order,
            description=excluded.description,
            assessment_status=excluded.assessment_status,
            verification_status=excluded.verification_status,
            source_doc_id=excluded.source_doc_id,
            source_page_start=excluded.source_page_start,
            source_page_end=excluded.source_page_end,
            source_section=excluded.source_section,
            metadata_json=excluded.metadata_json;
        """
        params = dict(topic_dict)
        params.setdefault("sequence_order", 1)
        params.setdefault("description", None)
        params.setdefault("source_doc_id", None)
        params.setdefault("source_page_start", None)
        params.setdefault("source_page_end", None)
        params.setdefault("source_section", None)
        meta = params.get("metadata_json") or params.get("metadata", {})
        params["metadata_json"] = json.dumps(meta) if isinstance(meta, (dict, list)) else str(meta or "{}")

        with self.db.get_connection() as conn:
            conn.execute(sql, params)

    def get_topics(self, chapter_id: Optional[str] = None) -> List[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            if chapter_id:
                cursor = conn.execute("SELECT * FROM topics WHERE chapter_id = ? ORDER BY sequence_order", (chapter_id,))
            else:
                cursor = conn.execute("SELECT * FROM topics ORDER BY chapter_id, sequence_order")
            return [dict(row) for row in cursor.fetchall()]

    # Subtopics
    def upsert_subtopic(self, sub_dict: Dict[str, Any]):
        sql = """
        INSERT INTO subtopics (
            subtopic_id, topic_id, name, sequence_order, description,
            assessment_status, verification_status, source_doc_id,
            source_page_start, source_page_end, source_section
        ) VALUES (
            :subtopic_id, :topic_id, :name, :sequence_order, :description,
            :assessment_status, :verification_status, :source_doc_id,
            :source_page_start, :source_page_end, :source_section
        ) ON CONFLICT(subtopic_id) DO UPDATE SET
            topic_id=excluded.topic_id,
            name=excluded.name,
            sequence_order=excluded.sequence_order,
            description=excluded.description,
            assessment_status=excluded.assessment_status,
            verification_status=excluded.verification_status,
            source_doc_id=excluded.source_doc_id,
            source_page_start=excluded.source_page_start,
            source_page_end=excluded.source_page_end,
            source_section=excluded.source_section;
        """
        params = dict(sub_dict)
        params.setdefault("sequence_order", 1)
        params.setdefault("description", None)
        params.setdefault("source_doc_id", None)
        params.setdefault("source_page_start", None)
        params.setdefault("source_page_end", None)
        params.setdefault("source_section", None)

        with self.db.get_connection() as conn:
            conn.execute(sql, params)

    def get_subtopics(self, topic_id: Optional[str] = None) -> List[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            if topic_id:
                cursor = conn.execute("SELECT * FROM subtopics WHERE topic_id = ? ORDER BY sequence_order", (topic_id,))
            else:
                cursor = conn.execute("SELECT * FROM subtopics ORDER BY topic_id, sequence_order")
            return [dict(row) for row in cursor.fetchall()]

    # Learning Outcomes
    def upsert_learning_outcome(self, lo_dict: Dict[str, Any]):
        sql = """
        INSERT INTO learning_outcomes (
            outcome_id, code, related_chapter_id, related_topic_id, description,
            curricular_goal, competency, suggestive_verbs_json, provenance_type,
            verification_status, source_doc_id, source_page, source_section
        ) VALUES (
            :outcome_id, :code, :related_chapter_id, :related_topic_id, :description,
            :curricular_goal, :competency, :suggestive_verbs_json, :provenance_type,
            :verification_status, :source_doc_id, :source_page, :source_section
        ) ON CONFLICT(outcome_id) DO UPDATE SET
            code=excluded.code,
            related_chapter_id=excluded.related_chapter_id,
            related_topic_id=excluded.related_topic_id,
            description=excluded.description,
            curricular_goal=excluded.curricular_goal,
            competency=excluded.competency,
            suggestive_verbs_json=excluded.suggestive_verbs_json,
            provenance_type=excluded.provenance_type,
            verification_status=excluded.verification_status,
            source_doc_id=excluded.source_doc_id,
            source_page=excluded.source_page,
            source_section=excluded.source_section;
        """
        params = dict(lo_dict)
        params.setdefault("code", None)
        params.setdefault("related_topic_id", None)
        params.setdefault("curricular_goal", None)
        params.setdefault("competency", None)
        params.setdefault("source_doc_id", None)
        params.setdefault("source_page", None)
        params.setdefault("source_section", None)
        verbs = params.get("suggestive_verbs_json") or params.get("suggestive_verbs", [])
        params["suggestive_verbs_json"] = json.dumps(verbs) if isinstance(verbs, list) else str(verbs or "[]")

        with self.db.get_connection() as conn:
            conn.execute(sql, params)

    def get_learning_outcomes(self, chapter_id: Optional[str] = None) -> List[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            if chapter_id:
                cursor = conn.execute("SELECT * FROM learning_outcomes WHERE related_chapter_id = ? ORDER BY outcome_id", (chapter_id,))
            else:
                cursor = conn.execute("SELECT * FROM learning_outcomes ORDER BY related_chapter_id, outcome_id")
            return [dict(row) for row in cursor.fetchall()]

    # Mappings
    def upsert_curriculum_mapping(self, map_dict: Dict[str, Any]):
        sql = """
        INSERT INTO curriculum_mappings (
            mapping_id, parent_type, parent_id, child_type, child_id,
            sequence_order, verification_status, notes
        ) VALUES (
            :mapping_id, :parent_type, :parent_id, :child_type, :child_id,
            :sequence_order, :verification_status, :notes
        ) ON CONFLICT(mapping_id) DO UPDATE SET
            parent_type=excluded.parent_type,
            parent_id=excluded.parent_id,
            child_type=excluded.child_type,
            child_id=excluded.child_id,
            sequence_order=excluded.sequence_order,
            verification_status=excluded.verification_status,
            notes=excluded.notes;
        """
        params = dict(map_dict)
        params.setdefault("sequence_order", 1)
        params.setdefault("notes", None)
        with self.db.get_connection() as conn:
            conn.execute(sql, params)

    def get_curriculum_mappings(self) -> List[Dict[str, Any]]:
        with self.db.get_connection() as conn:
            cursor = conn.execute("SELECT * FROM curriculum_mappings ORDER BY sequence_order")
            return [dict(row) for row in cursor.fetchall()]

    # Source Citations
    def upsert_citation(self, cit_dict: Dict[str, Any]):
        sql = """
        INSERT INTO source_citations (
            citation_id, entity_type, entity_id, document_id,
            page_start, page_end, section, verbatim_quote
        ) VALUES (
            :citation_id, :entity_type, :entity_id, :document_id,
            :page_start, :page_end, :section, :verbatim_quote
        ) ON CONFLICT(citation_id) DO UPDATE SET
            entity_type=excluded.entity_type,
            entity_id=excluded.entity_id,
            document_id=excluded.document_id,
            page_start=excluded.page_start,
            page_end=excluded.page_end,
            section=excluded.section,
            verbatim_quote=excluded.verbatim_quote;
        """
        params = dict(cit_dict)
        params.setdefault("page_start", None)
        params.setdefault("page_end", None)
        params.setdefault("section", None)
        params.setdefault("verbatim_quote", None)
        with self.db.get_connection() as conn:
            conn.execute(sql, params)
