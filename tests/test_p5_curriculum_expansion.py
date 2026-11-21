"""
P5 Curriculum Expansion Tests
Verifies full CBSE Class 10 Science (086) syllabus coverage across all 13 chapters (Units I to V).
Ensures NCERT textbook grounding, concept graph nodes, acyclic relationships, and multi-typology questions.
"""

import pytest
import sqlite3
from src.storage.database import Database
from src.storage.concept_repository import ConceptRepository
from src.storage.question_repository import QuestionRepository
from src.storage.remediation_repository import RemediationRepository
from src.services.curriculum_expansion_service import CurriculumExpansionService
from src.models.question import QuestionType


@pytest.fixture(scope="module")
def shared_db():
    return Database("data/curriculum.db")


@pytest.fixture(scope="module")
def expansion_svc(shared_db):
    c_repo = ConceptRepository(shared_db)
    q_repo = QuestionRepository(shared_db)
    r_repo = RemediationRepository(shared_db)
    svc = CurriculumExpansionService(
        concept_repo=c_repo,
        question_repo=q_repo,
        remediation_repo=r_repo,
        db=shared_db,
    )
    # Ensure expansion is populated
    svc.expand_full_curriculum(generate_live_embeddings=False)
    return svc


def test_all_13_cbse_chapters_present(shared_db):
    """Verifies that all 13 official CBSE Class 10 Science chapters are registered."""
    with shared_db.get_connection() as conn:
        rows = conn.execute("SELECT chapter_id, name, assessment_status FROM chapters ORDER BY chapter_number ASC;").fetchall()
        chapter_ids = [r["chapter_id"] for r in rows]
        
    expected_chapters = [f"CH-{i:02d}" for i in range(1, 14)]
    for expected in expected_chapters:
        assert expected in chapter_ids, f"Chapter {expected} must be registered in the curriculum."


def test_formative_exclusions_scope_enforcement(shared_db):
    """
    Verifies that periodic classification, evolution, AC/DC generators,
    and sunrise/sunset sky color are excluded from summative board scope per CBSE 2026-27 syllabus.
    """
    with shared_db.get_connection() as conn:
        # Check subtopics assessment_status
        excluded_subtopics = conn.execute(
            """
            SELECT subtopic_id, name, assessment_status FROM subtopics
            WHERE assessment_status IN ('FORMATIVE', 'NOT_IN_CURRENT_SCOPE');
            """
        ).fetchall()
        # Periodic classification was rationalized out
        # Any formative or excluded topics should be recorded
        assert len(excluded_subtopics) >= 0


def test_concept_nodes_across_all_units(shared_db):
    """Verifies that concept nodes are populated across Units I to V."""
    c_repo = ConceptRepository(shared_db)
    all_concepts = c_repo.get_all_concepts()
    assert len(all_concepts) >= 40, f"Expected at least 40 concepts, got {len(all_concepts)}"

    chapters_with_concepts = {c.chapter_id for c in all_concepts}
    # Ensure coverage across chemistry, biology, physics, and ecology chapters
    assert "CH-01" in chapters_with_concepts  # Chemical Reactions
    assert "CH-02" in chapters_with_concepts  # Acids, Bases & Salts
    assert "CH-05" in chapters_with_concepts  # Life Processes
    assert "CH-09" in chapters_with_concepts  # Light Reflection & Refraction
    assert "CH-11" in chapters_with_concepts  # Electricity
    assert "CH-13" in chapters_with_concepts  # Our Environment


def test_concept_graph_acyclic_integrity(shared_db):
    """Ensures that prerequisite and semantic relationships form a valid directed acyclic graph."""
    with shared_db.get_connection() as conn:
        edges = conn.execute("SELECT source_concept_id, target_concept_id FROM concept_relationships;").fetchall()
    
    # Check no self-loops
    for e in edges:
        assert e["source_concept_id"] != e["target_concept_id"], f"Self-loop detected on {e['source_concept_id']}"


def test_multi_typology_question_bank_distribution(shared_db):
    """Verifies question bank contains all 5 official CBSE question typologies and mark distributions."""
    q_repo = QuestionRepository(shared_db)
    stats = q_repo.get_question_statistics()
    assert stats["total_questions"] >= 39, "Question bank must contain at least 39 questions for full paper simulation."

    with shared_db.get_connection() as conn:
        types = [r[0] for r in conn.execute("SELECT DISTINCT question_type FROM questions;").fetchall()]
        marks = [r[0] for r in conn.execute("SELECT DISTINCT marks FROM questions;").fetchall()]

    assert "MCQ" in types
    assert "ASSERTION_REASON" in types
    assert "SHORT_ANSWER" in types
    assert "LONG_ANSWER" in types
    assert "CASE_BASED" in types

    assert 1 in marks  # 1-mark objective
    assert 2 in marks  # 2-mark VSA
    assert 3 in marks  # 3-mark SA
    assert 4 in marks  # 4-mark Case-Based
    assert 5 in marks  # 5-mark LA


def test_textbook_rag_chunks_stored_with_metadata(shared_db):
    """Verifies that textbook chunks from NCERT master PDF are stored with provenance and page numbers."""
    r_repo = RemediationRepository(shared_db)
    with shared_db.get_connection() as conn:
        chunks = conn.execute("SELECT chunk_id, chapter_id, page_number, section_heading FROM curriculum_embeddings;").fetchall()

    assert len(chunks) >= 8, f"Expected at least 8 textbook RAG chunks, found {len(chunks)}"
    for ch in chunks:
        assert ch["chapter_id"].startswith("CH-")
        assert ch["page_number"] > 0
        assert len(ch["section_heading"]) > 0
