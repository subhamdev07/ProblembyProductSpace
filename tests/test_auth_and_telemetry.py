"""
Test Suite for BodhAI Authentication and Student Activity Tracking
Verifies role-based authentication, student session management, fine-grained telemetry,
and real-time activity streams.
"""

import pytest
from starlette.testclient import TestClient
from src.api.app import app
from src.storage.database import Database
from src.storage.activity_repository import ActivityRepository
from src.services.activity_tracker_service import ActivityTrackerService
from src.services.auth_service import AuthService
from src.models.auth import LoginRequest


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def temp_db(tmp_path):
    db_file = tmp_path / "test_telemetry.db"
    return Database(str(db_file))


def test_login_page_served(client):
    """Verifies that the standalone BodhAI sign-in page is served at /login."""
    resp = client.get("/login")
    assert resp.status_code == 200
    assert "Sign in · BodhAI" in resp.text
    assert "aarav@bodhai.edu" in resp.text
    assert "Explore the demo experience" in resp.text or "Instant Demo Access Profiles" in resp.text


def test_student_authentication(client):
    """Tests student login with demo credentials."""
    resp = client.post(
        "/api/auth/login",
        json={"email": "aarav@bodhai.edu", "password": "password123", "role": "student"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["user"]["user_id"] == "STU-001"
    assert data["user"]["name"] == "Aarav Sharma"
    assert data["user"]["role"] == "student"
    assert data["token"].startswith("BODHAI-AUTH-")


def test_teacher_authentication(client):
    """Tests educator login with demo credentials."""
    resp = client.post(
        "/api/auth/login",
        json={"email": "sunita@bodhai.edu", "password": "password123", "role": "teacher"},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["user"]["user_id"] == "TCH-001"
    assert data["user"]["name"] == "Dr. Sunita Rao"
    assert data["user"]["role"] == "teacher"


def test_client_activity_logging_and_retrieval(client):
    """Tests posting client-side student activities and retrieving the chronological audit stream."""
    post_resp = client.post(
        "/api/student/activity",
        json={
            "student_id": "STU-001",
            "event_type": "STUDY_SESSION_TEST",
            "action_title": "Reviewed Chemical Reactions Flashcards",
            "details": {"chapter": "CH-01", "cards_reviewed": 8},
            "duration_seconds": 150,
        },
    )
    assert post_resp.status_code == 200
    assert post_resp.json()["status"] == "SUCCESS"

    get_resp = client.get("/api/student/STU-001/activity?limit=10")
    assert get_resp.status_code == 200
    items = get_resp.json()
    assert len(items) > 0
    assert any(item["event_type"] == "STUDY_SESSION_TEST" for item in items)


def test_student_telemetry_summary(client):
    """Tests calculating student engagement metrics."""
    resp = client.get("/api/student/STU-001/telemetry")
    assert resp.status_code == 200
    summary = resp.json()
    assert summary["student_id"] == "STU-001"
    assert summary["student_name"] == "Aarav Sharma"
    assert summary["total_activities"] >= 1
    assert "total_study_minutes" in summary


def test_teacher_activity_stream_access_control(client):
    """Verifies educator role authorization for classroom telemetry feed."""
    # Unauthorized role
    bad_resp = client.get("/api/teacher/activity-stream?role=student")
    assert bad_resp.status_code == 403

    # Authorized educator
    good_resp = client.get("/api/teacher/activity-stream?role=teacher")
    assert good_resp.status_code == 200
    feed = good_resp.json()
    assert isinstance(feed, list)
    assert len(feed) > 0
