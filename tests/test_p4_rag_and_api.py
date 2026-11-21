"""
Unit and Integration Tests for RAG & P4 REST API Endpoints
"""

import pytest
from fastapi.testclient import TestClient
from src.api.app import app
from src.storage.database import Database
from src.storage.remediation_repository import RemediationRepository
from src.services.rag_service import RAGService


@pytest.fixture
def api_client():
    return TestClient(app)


def test_rag_service_fallback_retrieval(tmp_path):
    db_file = tmp_path / "test_rag.db"
    db = Database(str(db_file))
    db.init_db()

    with db.get_connection() as conn:
        conn.execute("INSERT OR IGNORE INTO academic_sessions (session_id, name, start_year, end_year) VALUES ('SESS-2026-27', '2026-27', 2026, 2027);")
        conn.execute("INSERT OR IGNORE INTO subjects (subject_id, code, name, class_level) VALUES ('SUBJ-SCI-10', '086', 'Science', 10);")
        conn.execute("INSERT OR IGNORE INTO curricula (curriculum_id, name, session_id, subject_id) VALUES ('CURR-CBSE-10', 'CBSE Class 10 Science', 'SESS-2026-27', 'SUBJ-SCI-10');")
        conn.execute("INSERT OR IGNORE INTO units (unit_id, unit_number, name, curriculum_id, verification_status) VALUES ('UNIT-01', 'I', 'Chemical Substances', 'CURR-CBSE-10', 'VERIFIED');")
        conn.execute("INSERT OR IGNORE INTO chapters (chapter_id, chapter_number, name, unit_id, curriculum_id, assessment_status, verification_status) VALUES ('CH-01', 1, 'Chemical Reactions', 'UNIT-01', 'CURR-CBSE-10', 'SUMMATIVE', 'VERIFIED');")

    repo = RemediationRepository(db)
    repo.store_embedding_chunk(
        chunk_id="CHK-TEST-01",
        chapter_id="CH-01",
        topic_id=None,
        concept_id=None,
        source_doc_id=None,
        page_num=11,
        heading="Double Displacement & Precipitation",
        chunk_text="A white precipitate of barium sulphate forms when barium chloride reacts with sodium sulphate."
    )

    rag = RAGService(repo, api_key="dummy_key", model="dummy_model")
    results = rag.search_ncert_context("barium sulphate precipitate", top_k=1)

    assert len(results) == 1
    assert "barium sulphate" in results[0]["chunk_text"]
    assert results[0]["page_number"] == 11


def test_api_p4_misconceptions(api_client):
    res = api_client.get("/api/student/misconceptions?student_id=STU-001")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_api_p4_remediation(api_client):
    res = api_client.get("/api/student/remediation?student_id=STU-001")
    assert res.status_code == 200
    data = res.json()
    assert "remediation_id" in data
    assert "concept_name" in data
    assert "ncert_reference" in data


def test_api_p4_revision_endpoints(api_client):
    res = api_client.get("/api/student/revision-due?student_id=STU-001")
    assert res.status_code == 200
    assert isinstance(res.json(), list)

    res_up = api_client.get("/api/student/revision-upcoming?student_id=STU-001")
    assert res_up.status_code == 200
    assert isinstance(res_up.json(), list)


def test_api_p4_teacher_dashboard_authorization(api_client):
    # Teacher role allowed
    res_t = api_client.get("/api/teacher/dashboard?role=teacher")
    assert res_t.status_code == 200
    data = res_t.json()
    assert "total_students" in data
    assert "weakest_concepts" in data

    # Student role rejected with 403 Forbidden
    res_s = api_client.get("/api/teacher/dashboard?role=student")
    assert res_s.status_code == 403


def test_api_p4_rag_search(api_client):
    res = api_client.get("/api/rag/search?query=barium chloride")
    assert res.status_code == 200
    data = res.json()
    assert "results" in data
    assert data["query"] == "barium chloride"
