"""
Integration Tests for P3 BodhAI Full-Stack API
Tests all required REST API routes and the complete student journey via TestClient.
"""

import pytest
from fastapi.testclient import TestClient
from src.api.app import app


@pytest.fixture
def client():
    return TestClient(app)


def test_api_health_check(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "HEALTHY"
    assert data["question_bank_total"] >= 15


def test_api_student_dashboard(client):
    res = client.get("/api/student/dashboard?student_id=STU-001")
    assert res.status_code == 200
    data = res.json()
    assert data["student"]["student_id"] == "STU-001"
    assert "mastery_distribution" in data
    assert "overall_mastery_pct" in data


def test_api_assessment_lifecycle(client):
    # 1. Start assessment
    start_res = client.post(
        "/api/assessments/start",
        json={"student_id": "STU-001", "chapter_id": "CH-01", "question_count": 3},
    )
    assert start_res.status_code == 200
    session = start_res.json()
    asm_id = session["assessment_id"]
    assert len(session["questions"]) == 3

    # Verify student-facing views do not leak answer key or explanation
    for q in session["questions"]:
        assert "answer_key" not in q
        assert "explanation" not in q

    # 2. Get session state
    get_res = client.get(f"/api/assessments/{asm_id}")
    assert get_res.status_code == 200
    assert get_res.json()["assessment_id"] == asm_id

    # 3. Submit an answer for Q1
    q1 = session["questions"][0]
    ans_res = client.post(
        f"/api/assessments/{asm_id}/answers?student_id=STU-001",
        json={
            "question_id": q1["question_id"],
            "submitted_answer": {"selected_option": "C"},
            "time_spent_seconds": 20,
        },
    )
    assert ans_res.status_code == 200
    assert "is_correct" in ans_res.json()

    # 4. Finalize assessment
    sub_res = client.post(
        f"/api/assessments/{asm_id}/submit",
        json={"student_id": "STU-001"},
    )
    assert sub_res.status_code == 200
    summary = sub_res.json()
    assert summary["status"] == "EVALUATED"
    assert summary["total_questions"] == 3
    assert len(summary["question_reviews"]) == 3


def test_api_mastery_and_weak_concepts(client):
    # Mastery list
    res_m = client.get("/api/student/mastery?student_id=STU-001&chapter_id=CH-01")
    assert res_m.status_code == 200
    assert len(res_m.json()) == 29

    # Weak concepts endpoint
    res_w = client.get("/api/student/weak-concepts?student_id=STU-001")
    assert res_w.status_code == 200
    assert isinstance(res_w.json(), list)


def test_api_adaptive_next_question(client):
    res = client.get("/api/questions/next?student_id=STU-001&chapter_id=CH-01")
    assert res.status_code == 200
    data = res.json()
    assert "question" in data
    assert "selection_rationale" in data
    assert "target_concept_id" in data


def test_frontend_index_serving(client):
    res = client.get("/")
    assert res.status_code == 200
    assert "text/html" in res.headers["content-type"]
    assert "BodhAI" in res.text
    assert "Diagnostic Assessment" in res.text
