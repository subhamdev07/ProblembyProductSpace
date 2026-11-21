"""
BodhAI REST API Routes
Implements all student diagnostic assessment, learner mastery, targeted remediation,
spaced repetition, teacher dashboard, and NCERT RAG search endpoints.
"""

import re
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Query, Path, Header, Response
from pydantic import BaseModel, Field

from src.storage.database import Database
from src.storage.question_repository import QuestionRepository
from src.storage.assessment_repository import AssessmentRepository
from src.storage.learner_repository import LearnerRepository
from src.storage.concept_repository import ConceptRepository
from src.storage.remediation_repository import RemediationRepository
from src.storage.examination_repository import ExaminationRepository

from src.services.answer_evaluation_service import AnswerEvaluationService
from src.services.learner_model_service import LearnerModelService
from src.services.adaptive_selection_service import AdaptiveQuestionSelectionService
from src.services.diagnostic_assessment_service import DiagnosticAssessmentService
from src.services.misconception_detection_service import MisconceptionDetectionService
from src.services.spaced_repetition_service import SpacedRepetitionService
from src.services.targeted_remediation_service import TargetedRemediationService
from src.services.rag_service import RAGService
from src.services.teacher_dashboard_service import TeacherDashboardService
from src.services.examination_service import ExaminationService
from src.ai.llm_service import NVIDIANemotronService
from src.ai.groq_service import GroqService

from src.models.assessment import (
    AssessmentSession,
    SubmitAnswerRequest,
    AnswerEvaluationResult,
    AssessmentResultSummary,
)
from src.models.learner import (
    StudentDashboardData,
    ConceptMasteryItem,
    AdaptiveQuestionRecommendation,
)
from src.models.remediation import (
    StudentMisconceptionItem,
    TargetedRemediationPayload,
    CompleteRemediationRequest,
    CompleteRemediationResponse,
)
from src.models.spaced_repetition import (
    SpacedRepetitionItem,
    CompleteRevisionRequest,
    CompleteRevisionResponse,
)
from src.models.teacher import (
    TeacherDashboardData,
    TeacherStudentDetail,
)
from src.models.examination import (
    ExaminationStatus,
    ExaminationBlueprint,
    ExaminationSessionState,
    SaveExamAnswerRequest,
    SaveExamAnswerResponse,
    SubmitExamRequest,
    ExaminationResultSummary,
    ExaminationOverviewItem,
)
from src.storage.activity_repository import ActivityRepository
from src.services.activity_tracker_service import ActivityTrackerService
from src.services.auth_service import AuthService
from src.models.auth import LoginRequest, LoginResponse, UserProfile
from src.models.activity import StudentActivityLog, StudentTelemetrySummary, RecordActivityRequest

router = APIRouter(prefix="/api")

_db: Optional[Database] = None
_question_repo: Optional[QuestionRepository] = None
_assessment_repo: Optional[AssessmentRepository] = None
_learner_repo: Optional[LearnerRepository] = None
_concept_repo: Optional[ConceptRepository] = None
_remediation_repo: Optional[RemediationRepository] = None
_exam_repo: Optional[ExaminationRepository] = None
_activity_repo: Optional[ActivityRepository] = None

_evaluation_service: Optional[AnswerEvaluationService] = None
_learner_service: Optional[LearnerModelService] = None
_adaptive_service: Optional[AdaptiveQuestionSelectionService] = None
_misconception_service: Optional[MisconceptionDetectionService] = None
_spaced_repetition_service: Optional[SpacedRepetitionService] = None
_targeted_remediation_service: Optional[TargetedRemediationService] = None
_rag_service: Optional[RAGService] = None
_teacher_service: Optional[TeacherDashboardService] = None
_diagnostic_service: Optional[DiagnosticAssessmentService] = None
_examination_service: Optional[ExaminationService] = None
_activity_service: Optional[ActivityTrackerService] = None
_auth_service: Optional[AuthService] = None
_llm_service: Optional[NVIDIANemotronService] = None
_groq_service: Optional[GroqService] = None


def get_services(db_path: str = "data/curriculum.db"):
    global _db, _question_repo, _assessment_repo, _learner_repo, _concept_repo, _remediation_repo, _exam_repo, _activity_repo
    global _evaluation_service, _learner_service, _adaptive_service, _diagnostic_service
    global _misconception_service, _spaced_repetition_service, _targeted_remediation_service
    global _rag_service, _teacher_service, _examination_service, _activity_service, _auth_service, _llm_service, _groq_service

    if _db is None:
        _db = Database(db_path)
        _question_repo = QuestionRepository(_db)
        _assessment_repo = AssessmentRepository(_db)
        _learner_repo = LearnerRepository(_db)
        _concept_repo = ConceptRepository(_db)
        _remediation_repo = RemediationRepository(_db)
        _exam_repo = ExaminationRepository(_db)
        _activity_repo = ActivityRepository(_db)

        _learner_repo.get_or_create_student("STU-001", "Aarav Sharma", 10)
        _learner_repo.get_or_create_student("STU-002", "Priya Patel", 10)
        _learner_repo.get_or_create_student("STU-003", "Rohan Verma", 10)

        _llm_service = NVIDIANemotronService()
        _evaluation_service = AnswerEvaluationService(llm_service=_llm_service)
        _learner_service = LearnerModelService(_learner_repo, _assessment_repo, _concept_repo)
        _adaptive_service = AdaptiveQuestionSelectionService(_question_repo, _learner_repo, _concept_repo)
        _misconception_service = MisconceptionDetectionService(_remediation_repo, _question_repo, _concept_repo)
        _spaced_repetition_service = SpacedRepetitionService(_remediation_repo, _learner_repo, _concept_repo)
        _targeted_remediation_service = TargetedRemediationService(
            _remediation_repo,
            _learner_repo,
            _concept_repo,
            _question_repo,
            _evaluation_service,
            _misconception_service,
            _spaced_repetition_service,
        )
        _rag_service = RAGService(_remediation_repo)
        _teacher_service = TeacherDashboardService(_db, _learner_repo, _remediation_repo, _concept_repo)

        _diagnostic_service = DiagnosticAssessmentService(
            _assessment_repo,
            _question_repo,
            _evaluation_service,
            _learner_service,
            _misconception_service,
            _spaced_repetition_service,
        )

        _examination_service = ExaminationService(
            _db,
            _exam_repo,
            _question_repo,
            _concept_repo,
            _evaluation_service,
            _learner_service,
            _misconception_service,
            _spaced_repetition_service,
            _targeted_remediation_service,
            _learner_repo,
        )

        _activity_service = ActivityTrackerService(_db, _activity_repo)
        _auth_service = AuthService(_db, _learner_repo)
        _groq_service = GroqService()

        _activity_service.seed_initial_demo_activities_if_empty("STU-001", "Aarav Sharma")
        _activity_service.seed_initial_demo_activities_if_empty("STU-002", "Priya Patel")
        _activity_service.seed_initial_demo_activities_if_empty("STU-003", "Rohan Verma")

    return {
        "db": _db,
        "question_repo": _question_repo,
        "assessment_repo": _assessment_repo,
        "learner_repo": _learner_repo,
        "concept_repo": _concept_repo,
        "remediation_repo": _remediation_repo,
        "exam_repo": _exam_repo,
        "activity_repo": _activity_repo,
        "evaluation_service": _evaluation_service,
        "learner_service": _learner_service,
        "adaptive_service": _adaptive_service,
        "misconception_service": _misconception_service,
        "spaced_repetition_service": _spaced_repetition_service,
        "targeted_remediation_service": _targeted_remediation_service,
        "rag_service": _rag_service,
        "teacher_service": _teacher_service,
        "diagnostic_service": _diagnostic_service,
        "examination_service": _examination_service,
        "activity_service": _activity_service,
        "auth_service": _auth_service,
        "llm_service": _llm_service,
        "groq_service": _groq_service,
    }


class StartAssessmentRequest(BaseModel):
    student_id: str = Field(default="STU-001")
    chapter_id: str = Field(default="CH-01")
    question_count: int = Field(default=5, ge=1, le=15)


class FinalizeAssessmentRequest(BaseModel):
    student_id: str = Field(default="STU-001")


@router.get("/health")
def health_check():
    svcs = get_services()
    stats = svcs["question_repo"].get_question_statistics()
    return {
        "status": "HEALTHY",
        "service": "BodhAI Adaptive Learning API",
        "curriculum": "CBSE Class 10 Science (2026-27)",
        "question_bank_total": stats.get("total_questions", 0),
        "chapter_covered": "CH-01 Chemical Reactions and Equations",
        "features": [
            "Diagnostic Assessment",
            "Concept Graph DAG",
            "Learner Model",
            "Evidence-based Misconceptions",
            "Targeted Remediation",
            "Spaced Repetition",
            "Teacher Dashboard",
            "Supabase pgvector RAG",
        ],
    }


@router.post("/auth/login", response_model=LoginResponse)
def login_user(payload: LoginRequest, response: Response):
    svcs = get_services()
    resp = svcs["auth_service"].authenticate(payload)
    if resp.success and resp.user.user_id:
        response.set_cookie(key="bodhai_role", value=resp.user.role, path="/")
        response.set_cookie(key="bodhai_user_id", value=resp.user.user_id, path="/")
        if resp.token:
            response.set_cookie(key="bodhai_token", value=resp.token, path="/")
        svcs["activity_service"].record_event(
            student_id=resp.user.user_id,
            event_type="AUTH_LOGIN",
            action_title=f"Logged in as {resp.user.name} ({resp.user.role})",
            details={"email": resp.user.email, "role": resp.user.role, "grade": resp.user.grade},
            duration_seconds=60,
        )
    return resp


@router.post("/auth/guest", response_model=LoginResponse)
def login_as_guest(response: Response):
    """Provisions a fresh guest student account (STU-GUEST), clears prior guest attempts, and logs in."""
    import uuid
    svcs = get_services()
    guest_id = "STU-GUEST"
    guest_name = "Guest Student"
    guest_email = "guest@bodhai.edu"

    with svcs["db"].get_connection() as conn:
        conn.execute("DELETE FROM learner_concept_mastery WHERE student_id = ?;", (guest_id,))
        conn.execute("DELETE FROM student_misconceptions WHERE student_id = ?;", (guest_id,))
        conn.execute("DELETE FROM spaced_repetition_schedules WHERE student_id = ?;", (guest_id,))
        conn.execute("DELETE FROM remediation_records WHERE student_id = ?;", (guest_id,))
        conn.execute("DELETE FROM assessments WHERE student_id = ?;", (guest_id,))
        conn.execute("DELETE FROM student_answers WHERE student_id = ?;", (guest_id,))
        conn.execute("DELETE FROM examination_sessions WHERE student_id = ?;", (guest_id,))
        conn.execute("DELETE FROM examination_answers WHERE student_id = ?;", (guest_id,))
        conn.execute("DELETE FROM examination_results WHERE student_id = ?;", (guest_id,))
        conn.execute("DELETE FROM student_activity_logs WHERE student_id = ?;", (guest_id,))

        conn.execute(
            "INSERT INTO students (student_id, name, grade) VALUES (?, ?, ?)"
            " ON CONFLICT(student_id) DO UPDATE SET name=excluded.name;",
            (guest_id, guest_name, 10),
        )
        conn.execute(
            """
            INSERT INTO users (user_id, name, email, role, grade, password_hash, avatar, school)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                name=excluded.name,
                email=excluded.email,
                role=excluded.role,
                grade=excluded.grade,
                password_hash=excluded.password_hash,
                avatar=excluded.avatar,
                school=excluded.school;
            """,
            (guest_id, guest_name, guest_email, "student", 10, "password123", "GS", "BodhAI Open Learning"),
        )

        conn.execute(
            """
            INSERT INTO spaced_repetition_schedules (
                schedule_id, student_id, concept_id, last_reviewed_at, next_review_at,
                interval_days, ease_factor, review_count, last_result, current_mastery,
                review_status, created_at, updated_at
            )
            SELECT 
                'REV-GUEST-' || substr(schedule_id, 5),
                ?,
                concept_id,
                last_reviewed_at,
                next_review_at,
                interval_days,
                ease_factor,
                review_count,
                last_result,
                current_mastery,
                review_status,
                CURRENT_TIMESTAMP,
                CURRENT_TIMESTAMP
            FROM spaced_repetition_schedules
            WHERE student_id = 'STU-001';
            """,
            (guest_id,),
        )
        conn.commit()

    token = f"BODHAI-AUTH-GUEST-{uuid.uuid4().hex[:12]}"
    user = UserProfile(
        user_id=guest_id,
        name=guest_name,
        email=guest_email,
        role="student",
        grade=10,
        avatar="GS",
        school="BodhAI Open Learning",
    )

    response.set_cookie(key="bodhai_role", value="student", path="/")
    response.set_cookie(key="bodhai_user_id", value=guest_id, path="/")
    response.set_cookie(key="bodhai_token", value=token, path="/")

    svcs["activity_service"].record_event(
        student_id=guest_id,
        event_type="AUTH_GUEST_LOGIN",
        action_title=f"Guest session started as {guest_name}",
        details={"role": "student", "is_guest": True},
        duration_seconds=60,
    )

    return LoginResponse(
        success=True,
        message=f"Welcome, {guest_name}! Starting fresh session.",
        token=token,
        user=user,
    )


@router.post("/auth/logout")
def logout_user_api(response: Response):
    response.delete_cookie("bodhai_role", path="/")
    response.delete_cookie("bodhai_user_id", path="/")
    response.delete_cookie("bodhai_token", path="/")
    return {"success": True, "message": "Logged out successfully"}


@router.get("/auth/me")
def get_current_user_profile(
    student_id: str = Query("STU-001"), role: str = Query("student")
):
    """Returns active user session profile with school and role details."""
    svcs = get_services()
    if role.lower() in ("teacher", "educator"):
        return {
            "user_id": "TCH-001",
            "name": "Dr. Sunita Rao",
            "email": "sunita@bodhai.edu",
            "role": "teacher",
            "avatar": "SR",
            "school": "National Science Teachers Association",
        }
    stu = svcs["learner_repo"].get_student(student_id) or svcs["learner_repo"].get_or_create_student(student_id)
    return {
        "user_id": stu.student_id,
        "name": stu.name,
        "email": f"{stu.name.lower().replace(' ', '.')}@bodhai.edu",
        "role": "student",
        "grade": stu.grade or 10,
        "avatar": "".join([part[0] for part in stu.name.split()[:2]]).upper(),
        "school": "Delhi Public School, R.K. Puram",
    }


@router.post("/student/activity")
def record_student_activity(payload: RecordActivityRequest):
    """Client-side telemetry hook to track every student action."""
    svcs = get_services()
    log_id = svcs["activity_service"].record_event(
        student_id=payload.student_id,
        event_type=payload.event_type,
        action_title=payload.action_title,
        details=payload.details,
        duration_seconds=payload.duration_seconds or 0,
    )
    return {"status": "SUCCESS", "log_id": log_id}


@router.get("/student/{student_id}/activity", response_model=List[StudentActivityLog])
def get_student_activity_timeline(
    student_id: str = Path(...), limit: int = Query(50, ge=1, le=200)
):
    """Returns chronologically ordered student telemetry audit stream."""
    svcs = get_services()
    return svcs["activity_service"].get_timeline(student_id=student_id, limit=limit)


@router.get("/student/{student_id}/telemetry", response_model=StudentTelemetrySummary)
def get_student_telemetry_summary(student_id: str = Path(...)):
    """Computes comprehensive student engagement telemetry metrics."""
    svcs = get_services()
    stu = svcs["learner_repo"].get_student(student_id)
    name = stu.name if stu else "Student"
    return svcs["activity_service"].get_summary(student_id=student_id, student_name=name)


@router.get("/teacher/activity-stream")
def get_classroom_activity_feed(
    limit: int = Query(100, ge=1, le=500),
    role: str = Query("teacher"),
    x_role: Optional[str] = Header(None, alias="X-Role"),
):
    """Live classroom telemetry feed for teacher dashboard."""
    svcs = get_services()
    effective_role = x_role or role
    try:
        svcs["teacher_service"]._verify_teacher_role(effective_role)
        return svcs["activity_service"].get_classroom_feed(limit=limit)
    except PermissionError as pe:
        raise HTTPException(status_code=403, detail=str(pe))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Activity feed error: {str(e)}")


@router.get("/student/dashboard", response_model=StudentDashboardData)
def get_student_dashboard(student_id: str = Query("STU-001")):
    if student_id and str(student_id).upper().startswith("TCH"):
        raise HTTPException(status_code=403, detail="Teachers cannot access student dashboard.")
    svcs = get_services()
    try:
        return svcs["learner_service"].get_student_dashboard(student_id=student_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch dashboard: {str(e)}")


@router.post("/assessments/start", response_model=AssessmentSession)
def start_assessment(payload: StartAssessmentRequest):
    if payload.student_id and str(payload.student_id).upper().startswith("TCH"):
        raise HTTPException(status_code=403, detail="Teachers cannot attempt student diagnostic assessments.")
    svcs = get_services()
    try:
        session = svcs["diagnostic_service"].start_diagnostic_assessment(
            student_id=payload.student_id,
            chapter_id=payload.chapter_id,
            question_count=payload.question_count,
        )
        return session
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Cannot start assessment: {str(e)}")


@router.get("/assessments/{assessment_id}", response_model=AssessmentSession)
def get_assessment(assessment_id: str = Path(...)):
    svcs = get_services()
    session = svcs["diagnostic_service"].get_assessment_session(assessment_id)
    if not session:
        raise HTTPException(status_code=404, detail=f"Assessment '{assessment_id}' not found.")
    return session


@router.post("/assessments/{assessment_id}/answers", response_model=AnswerEvaluationResult)
def submit_answer(
    assessment_id: str = Path(...),
    payload: SubmitAnswerRequest = ...,
    student_id: Optional[str] = Query(None)
):
    svcs = get_services()
    try:
        sid = student_id or payload.student_id
        if not sid:
            sess = svcs["diagnostic_service"].get_assessment_session(assessment_id)
            sid = sess.student_id if sess else "STU-001"
        result = svcs["diagnostic_service"].submit_answer(
            assessment_id=assessment_id,
            student_id=sid,
            question_id=payload.question_id,
            submitted_answer=payload.submitted_answer,
            time_spent_seconds=payload.time_spent_seconds,
        )
        svcs["activity_service"].record_event(
            student_id=sid,
            event_type="QUESTION_ATTEMPT",
            action_title=f"Answered Diagnostic Question ({'Correct' if result.is_correct else 'Incorrect'})",
            details={
                "assessment_id": assessment_id,
                "question_id": payload.question_id,
                "is_correct": result.is_correct,
                "marks_awarded": result.marks_awarded,
                "misconceptions": result.detected_misconceptions,
            },
            duration_seconds=payload.time_spent_seconds or 30,
        )
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Answer submission error: {str(e)}")


@router.post("/assessments/{assessment_id}/submit", response_model=AssessmentResultSummary)
def finalize_assessment(assessment_id: str = Path(...), payload: FinalizeAssessmentRequest = ...):
    svcs = get_services()
    try:
        summary = svcs["diagnostic_service"].submit_final_assessment(
            assessment_id=assessment_id, student_id=payload.student_id
        )
        svcs["activity_service"].record_event(
            student_id=payload.student_id,
            event_type="DIAGNOSTIC_ASSESSMENT_SUBMIT",
            action_title=f"Submitted Diagnostic Assessment — Score: {summary.score}/{summary.total_marks} ({summary.percentage}%)",
            details={
                "assessment_id": assessment_id,
                "total_score": summary.score,
                "max_score": summary.total_marks,
                "accuracy_percentage": summary.percentage,
                "concepts_mastered": len(summary.strong_concepts),
                "weak_concepts": len(summary.weak_concepts),
            },
            duration_seconds=240,
        )
        return summary
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Finalization error: {str(e)}")


@router.get("/student/mastery", response_model=List[ConceptMasteryItem])
def get_student_mastery(
    student_id: str = Query("STU-001"), chapter_id: Optional[str] = Query("CH-01")
):
    svcs = get_services()
    return svcs["learner_repo"].get_all_concept_mastery(
        student_id=student_id, chapter_id=chapter_id
    )


@router.get("/student/weak-concepts", response_model=List[ConceptMasteryItem])
def get_weak_concepts(
    student_id: str = Query("STU-001"), chapter_id: Optional[str] = Query("CH-01")
):
    svcs = get_services()
    all_m = svcs["learner_repo"].get_all_concept_mastery(
        student_id=student_id, chapter_id=chapter_id
    )
    return [m for m in all_m if m.total_attempts > 0 and m.mastery_score < 0.5]


@router.get("/student/assessment-history")
def get_assessment_history(
    student_id: str = Query("STU-001"), limit: int = Query(10, ge=1, le=50)
):
    svcs = get_services()
    return svcs["assessment_repo"].get_student_assessment_history(
        student_id=student_id, limit=limit
    )


@router.get("/questions/next", response_model=AdaptiveQuestionRecommendation)
def get_next_question(
    student_id: str = Query("STU-001"),
    chapter_id: str = Query("CH-01"),
    exclude: Optional[str] = Query(None, description="Comma-separated question IDs to exclude"),
):
    if student_id and str(student_id).upper().startswith("TCH"):
        raise HTTPException(status_code=403, detail="Teachers cannot access adaptive practice.")
    svcs = get_services()
    exclude_list = [x.strip() for x in exclude.split(",") if x.strip()] if exclude else []
    try:
        rec = svcs["adaptive_service"].select_next_question(
            student_id=student_id,
            chapter_id=chapter_id,
            exclude_question_ids=exclude_list,
        )
        return rec
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Adaptive selection failed: {str(e)}")


@router.get("/student/misconceptions", response_model=List[StudentMisconceptionItem])
def get_student_misconceptions(
    student_id: str = Query("STU-001"), status: Optional[str] = Query(None)
):
    if student_id and str(student_id).upper().startswith("TCH"):
        raise HTTPException(status_code=403, detail="Teachers cannot access student misconceptions.")
    svcs = get_services()
    items = svcs["misconception_service"].get_student_misconceptions(student_id, status)
    q_repo = svcs["question_repo"]
    for item in items:
        ev_list = []
        if item.evidence_text:
            raw_blocks = [b.strip() for b in item.evidence_text.split("||") if b.strip()]
            for block in raw_blocks:
                q_id_match = re.search(r"Q-[A-Za-z0-9_-]+", block)
                if not q_id_match:
                    continue
                qid = q_id_match.group(0)
                sub_match = re.search(r"selected_option['\"]\s*:\s*['\"]([A-Da-d])['\"]", block)
                if not sub_match:
                    sub_match = re.search(r"Submitted answer:\s*['\"]([A-Da-d])['\"]", block)
                selected_opt = sub_match.group(1).upper() if sub_match else None
                q_obj = q_repo.get_question(qid)
                if q_obj:
                    opts = q_obj.answer_key.get("options", {}) if isinstance(q_obj.answer_key, dict) else {}
                    corr = q_obj.answer_key.get("correct_option") if isinstance(q_obj.answer_key, dict) else None
                    ev_list.append({
                        "question_id": q_obj.question_id,
                        "question_text": q_obj.question_text,
                        "options": opts,
                        "correct_option": corr,
                        "student_selected_option": selected_opt,
                        "student_answer_text": opts.get(selected_opt) if selected_opt and isinstance(opts, dict) else None,
                        "correct_answer_text": opts.get(corr) if corr and isinstance(opts, dict) else None,
                        "explanation": q_obj.explanation or "",
                        "difficulty": q_obj.difficulty.value if hasattr(q_obj.difficulty, "value") else str(q_obj.difficulty),
                        "marks": q_obj.marks
                    })
        item.parsed_evidences = ev_list
    return items


@router.get("/student/misconceptions/summary")
def get_misconceptions_summary():
    svcs = get_services()
    return svcs["misconception_service"].get_misconception_summary_by_cohort()


@router.get("/student/remediation", response_model=TargetedRemediationPayload)
def get_remediation_package(
    student_id: str = Query("STU-001"), concept_id: Optional[str] = Query(None)
):
    if student_id and str(student_id).upper().startswith("TCH"):
        raise HTTPException(status_code=403, detail="Teachers cannot access student remediation.")
    svcs = get_services()
    try:
        return svcs["targeted_remediation_service"].get_remediation_for_student(
            student_id=student_id, concept_id=concept_id
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate remediation: {str(e)}")


@router.post("/student/remediation/complete", response_model=CompleteRemediationResponse)
def complete_remediation(payload: CompleteRemediationRequest):
    svcs = get_services()
    try:
        resp = svcs["targeted_remediation_service"].complete_remediation_practice(
            remediation_id=payload.remediation_id,
            student_id=payload.student_id,
            question_id=payload.question_id,
            student_answer=payload.student_answer,
        )
        svcs["activity_service"].record_event(
            student_id=payload.student_id,
            event_type="REMEDIATION_STEP_COMPLETE",
            action_title=f"Completed Remediation Practice ({'Mastered' if resp.is_correct else 'Needs Review'})",
            details={
                "remediation_id": payload.remediation_id,
                "concept_id": resp.concept_id,
                "is_correct": resp.is_correct,
                "mastery_before": resp.mastery_before,
                "mastery_after": resp.mastery_after,
            },
            duration_seconds=120,
        )
        return resp
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to complete remediation: {str(e)}")


def _ensure_guest_revision_schedules(db: Database):
    with db.get_connection() as conn:
        count = conn.execute("SELECT COUNT(*) FROM spaced_repetition_schedules WHERE student_id = 'STU-GUEST';").fetchone()[0]
        if count == 0:
            conn.execute("INSERT OR IGNORE INTO students (student_id, name, grade) VALUES ('STU-GUEST', 'Guest Student', 10);")
            conn.execute(
                """
                INSERT OR IGNORE INTO spaced_repetition_schedules (
                    schedule_id, student_id, concept_id, last_reviewed_at, next_review_at,
                    interval_days, ease_factor, review_count, last_result, current_mastery,
                    review_status, created_at, updated_at
                )
                SELECT 
                    'REV-GUEST-' || substr(schedule_id, 5),
                    'STU-GUEST',
                    concept_id,
                    last_reviewed_at,
                    next_review_at,
                    interval_days,
                    ease_factor,
                    review_count,
                    last_result,
                    current_mastery,
                    review_status,
                    CURRENT_TIMESTAMP,
                    CURRENT_TIMESTAMP
                FROM spaced_repetition_schedules
                WHERE student_id = 'STU-001';
                """
            )
            conn.commit()


@router.get("/student/revision-due", response_model=List[SpacedRepetitionItem])
def get_due_revisions(student_id: str = Query("STU-001")):
    if student_id and str(student_id).upper().startswith("TCH"):
        raise HTTPException(status_code=403, detail="Teachers cannot access student revision schedules.")
    svcs = get_services()
    if student_id == "STU-GUEST":
        _ensure_guest_revision_schedules(svcs["db"])
    svcs["spaced_repetition_service"].sync_weak_concepts_to_schedule(student_id)
    return svcs["spaced_repetition_service"].get_due_revisions(student_id)


@router.get("/student/revision-upcoming", response_model=List[SpacedRepetitionItem])
def get_upcoming_revisions(student_id: str = Query("STU-001")):
    if student_id and str(student_id).upper().startswith("TCH"):
        raise HTTPException(status_code=403, detail="Teachers cannot access student revision schedules.")
    svcs = get_services()
    if student_id == "STU-GUEST":
        _ensure_guest_revision_schedules(svcs["db"])
    svcs["spaced_repetition_service"].sync_weak_concepts_to_schedule(student_id)
    return svcs["spaced_repetition_service"].get_upcoming_revisions(student_id)


@router.post("/student/revision/complete", response_model=CompleteRevisionResponse)
def complete_revision(payload: CompleteRevisionRequest):
    svcs = get_services()
    try:
        resp = svcs["spaced_repetition_service"].complete_revision(
            student_id=payload.student_id,
            concept_id=payload.concept_id,
            is_correct=payload.is_correct,
            difficulty_rating=payload.difficulty_rating or "NORMAL",
        )
        svcs["activity_service"].record_event(
            student_id=payload.student_id,
            event_type="SPACED_REPETITION_REVIEW",
            action_title=f"Completed Spaced Repetition Review ({'Correct' if payload.is_correct else 'Incorrect'})",
            details={
                "concept_id": payload.concept_id,
                "is_correct": payload.is_correct,
                "interval_days": resp.new_interval_days,
                "mastery": resp.new_mastery,
            },
            duration_seconds=60,
        )
        return resp
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to complete revision: {str(e)}")


@router.get("/teacher/dashboard", response_model=TeacherDashboardData)
def get_teacher_dashboard(
    role: str = Query("teacher", description="Role verification: teacher/educator/admin"),
    x_role: Optional[str] = Header(None, alias="X-Role"),
):
    svcs = get_services()
    effective_role = x_role or role
    try:
        return svcs["teacher_service"].get_dashboard_summary(role=effective_role)
    except PermissionError as pe:
        raise HTTPException(status_code=403, detail=str(pe))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Teacher dashboard error: {str(e)}")


@router.get("/teacher/students")
def get_teacher_students(
    role: str = Query("teacher"), x_role: Optional[str] = Header(None, alias="X-Role")
):
    svcs = get_services()
    effective_role = x_role or role
    try:
        return svcs["teacher_service"].get_all_students_overview(role=effective_role)
    except PermissionError as pe:
        raise HTTPException(status_code=403, detail=str(pe))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Teacher students error: {str(e)}")


@router.get("/teacher/students/{student_id}", response_model=TeacherStudentDetail)
def get_teacher_student_detail(
    student_id: str = Path(...),
    role: str = Query("teacher"),
    x_role: Optional[str] = Header(None, alias="X-Role"),
):
    svcs = get_services()
    effective_role = x_role or role
    try:
        return svcs["teacher_service"].get_student_drilldown(
            student_id=student_id, role=effective_role
        )
    except PermissionError as pe:
        raise HTTPException(status_code=403, detail=str(pe))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Student detail error: {str(e)}")


@router.get("/teacher/misconceptions")
def get_teacher_misconceptions(
    role: str = Query("teacher"), x_role: Optional[str] = Header(None, alias="X-Role")
):
    svcs = get_services()
    effective_role = x_role or role
    try:
        svcs["teacher_service"]._verify_teacher_role(effective_role)
        return svcs["misconception_service"].get_misconception_summary_by_cohort()
    except PermissionError as pe:
        raise HTTPException(status_code=403, detail=str(pe))


@router.get("/teacher/concept-performance")
def get_teacher_concept_performance(
    role: str = Query("teacher"), x_role: Optional[str] = Header(None, alias="X-Role")
):
    svcs = get_services()
    effective_role = x_role or role
    try:
        summary = svcs["teacher_service"].get_dashboard_summary(role=effective_role)
        return summary.chapter_performance
    except PermissionError as pe:
        raise HTTPException(status_code=403, detail=str(pe))


@router.get("/rag/search")
def search_rag_context(
    query: str = Query(..., min_length=2), top_k: int = Query(3, ge=1, le=10)
):
    svcs = get_services()
    try:
        results = svcs["rag_service"].search_ncert_context(query=query, top_k=top_k)
        return {
            "query": query,
            "top_k": top_k,
            "results_count": len(results),
            "results": results,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"RAG search error: {str(e)}")


class DoubtSolverRequest(BaseModel):
    question: str = Field(..., min_length=2, description="Student's science doubt or question")
    student_id: Optional[str] = Field("STU-001")
    chapter_id: Optional[str] = Field("CH-01")


class DoubtSolverResponse(BaseModel):
    question: str
    answer: str
    ncert_citations: List[Dict[str, Any]] = Field(default_factory=list)
    suggested_followups: List[str] = Field(default_factory=list)
    model: str = "nvidia/nemotron-3.5-lightning-30b-a3b"


@router.post("/ai/doubt-solver", response_model=DoubtSolverResponse)
def solve_student_doubt(payload: DoubtSolverRequest):
    svcs = get_services()
    rag_svc = svcs.get("rag_service")
    llm_svc = svcs.get("llm_service")
    groq_svc = svcs.get("groq_service")
    rem_repo = svcs.get("remediation_repo")

    citations = []
    retrieved_text = ""
    try:
        if rag_svc:
            rag_results = rag_svc.search_ncert_context(query=payload.question, top_k=3)
            for r in rag_results:
                citations.append({
                    "section": r.get("section_heading", "NCERT Class 10 Science"),
                    "page": r.get("page_number", 1),
                    "excerpt": r.get("chunk_text", "")[:220] + "..."
                })
                retrieved_text += f"\n[Section: {r.get('section_heading')}, Page {r.get('page_number')}]: {r.get('chunk_text')}\n"
    except Exception:
        pass

    student_misconceptions = []
    try:
        if rem_repo and payload.student_id:
            active_m = rem_repo.get_student_misconceptions(payload.student_id)
            for m in active_m:
                student_misconceptions.append(f"- Concept: {m.concept_name} | Misconception: {m.description}")
    except Exception:
        pass

    misconception_info = (
        "Active Misconceptions / Learning Gaps for this Student:\n" + "\n".join(student_misconceptions)
        if student_misconceptions
        else "No critical misconceptions recorded yet for this student."
    )

    followups = [
        "Can you explain with a real-life example?",
        "What chemical equation represents this?",
        "What are common CBSE board questions on this concept?"
    ]

    prompt = f"""You are BodhAI, an expert CBSE Class 10 Science AI Tutor.
The student has asked the following doubt:
"{payload.question}"

Student Profile & Active Misconceptions:
{misconception_info}

Ground your explanation STRICTLY in the official NCERT Class 10 Science textbook.
Verified NCERT Context:
{retrieved_text if retrieved_text else "NCERT Class 10 Science Curriculum"}

Pedagogical Instructions:
1. Provide a clear, intuitive, and scientifically accurate answer suitable for a Class 10 student.
2. If the doubt touches upon any of the student's active misconceptions, address that misconception gently and resolve it.
3. If chemical reactions or formulas are involved, write them clearly in LaTeX ($...$ or $$...$$).
4. Highlight common misconceptions or board exam tips related to this concept.
5. Conclude with an encouraging tone.
"""
    answer_text = ""
    used_model = "Groq Llama-3.3-70B-Versatile"

    if groq_svc and groq_svc.is_configured:
        try:
            answer_text = groq_svc.generate(
                messages=[
                    {"role": "system", "content": "You are BodhAI, an expert CBSE Class 10 Science tutor. Ground all explanations in NCERT concepts and clarify student misconceptions."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=800,
            )
            used_model = groq_svc.model
        except Exception:
            pass

    if not answer_text and llm_svc and llm_svc.config.is_configured:
        try:
            resp = llm_svc.generate(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=700,
            )
            answer_text = resp.content.strip()
            used_model = llm_svc.config.model
        except Exception:
            pass

    if not answer_text:
        if citations:
            best_chunk = citations[0]["excerpt"]
            answer_text = (
                f"**According to NCERT Class 10 Science ({citations[0]['section']}, Page {citations[0]['page']}):**\n\n"
                f"{best_chunk}\n\n"
                f"**Key Conceptual Takeaway:** Always refer to the verified chemical equations and principles outlined in your NCERT textbook for authentic Board Examination answers."
            )
        else:
            answer_text = (
                f"According to NCERT Class 10 Science, scientific concepts must be approached by analyzing foundational principles, "
                f"balanced chemical equations, and experimental observations. Please refer to Chapter 1 for foundational reaction typologies."
            )

    return DoubtSolverResponse(
        question=payload.question,
        answer=answer_text,
        ncert_citations=citations,
        suggested_followups=followups,
        model=used_model
    )


@router.get("/concept-graph")
def get_concept_graph(
    student_id: str = Query("STU-001"),
    chapter_id: Optional[str] = Query(None),
):
    if student_id and str(student_id).upper().startswith("TCH"):
        raise HTTPException(status_code=403, detail="Teachers cannot access student concept graph.")
    svcs = get_services()
    concept_repo = svcs["concept_repo"]
    learner_repo = svcs["learner_repo"]
    remediation_repo = svcs["remediation_repo"]

    valid_chapter = chapter_id if (isinstance(chapter_id, str) and chapter_id.strip()) else None
    valid_student_id = student_id if (isinstance(student_id, str) and student_id.strip()) else "STU-001"

    concepts = concept_repo.get_concepts_by_chapter(valid_chapter) if valid_chapter else concept_repo.get_all_concepts()
    edges = concept_repo.get_all_edges()
    mastery_items = {item.concept_id: item for item in learner_repo.get_all_concept_mastery(valid_student_id)}
    active_misconceptions = {m.concept_id for m in remediation_repo.get_student_misconceptions(valid_student_id)}

    concept_ids = {c.concept_id for c in concepts}
    nodes = []
    for c in concepts:
        m = mastery_items.get(c.concept_id)
        mastery_score = m.mastery_score if m else 0.0
        status = m.status.value if (m and m.status) else "NOT_ASSESSED"
        has_misconception = c.concept_id in active_misconceptions
        diff_val = c.difficulty_level.value if hasattr(c.difficulty_level, "value") else str(c.difficulty_level)
        nodes.append({
            "id": c.concept_id,
            "name": c.name,
            "canonical_name": c.canonical_name,
            "chapter_id": c.chapter_id,
            "difficulty": diff_val,
            "mastery_score": round(mastery_score, 2),
            "status": status,
            "has_misconception": has_misconception,
            "description": c.description or "",
        })

    filtered_edges = []
    for e in edges:
        if e.source_concept_id in concept_ids and e.target_concept_id in concept_ids:
            rel_type = e.relationship_type.value if hasattr(e.relationship_type, "value") else str(e.relationship_type)
            filtered_edges.append({
                "source": e.source_concept_id,
                "target": e.target_concept_id,
                "relationship_type": rel_type,
            })

    all_all = concept_repo.get_all_concepts()
    chapters = sorted(list({c.chapter_id for c in all_all}))

    return {
        "nodes": nodes,
        "edges": filtered_edges,
        "chapters": chapters,
        "student_id": student_id,
    }


class StartExamRequest(BaseModel):
    student_id: str = "STU-001"
    blueprint_id: str = "BP-CBSE-X-SCI-2027"


@router.get("/examinations/blueprints", response_model=List[ExaminationBlueprint])
def get_examination_blueprints():
    """Returns all available official and mock examination blueprints."""
    svcs = get_services()
    try:
        return svcs["examination_service"].get_available_blueprints()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch blueprints: {str(e)}")


@router.get("/examinations/blueprints/{blueprint_id}", response_model=ExaminationBlueprint)
def get_examination_blueprint_details(blueprint_id: str = Path(...)):
    """Returns detailed structure for a specified blueprint."""
    svcs = get_services()
    bp = svcs["examination_service"].get_blueprint_details(blueprint_id)
    if not bp:
        raise HTTPException(status_code=404, detail=f"Blueprint {blueprint_id} not found.")
    return bp


@router.post("/examinations/start", response_model=ExaminationSessionState)
def start_or_resume_examination(req: StartExamRequest):
    if req.student_id and str(req.student_id).upper().startswith("TCH"):
        raise HTTPException(status_code=403, detail="Teachers cannot sit for board examination simulations.")
    svcs = get_services()
    try:
        sess_state = svcs["examination_service"].start_examination(
            student_id=req.student_id,
            blueprint_id=req.blueprint_id,
        )
        svcs["activity_service"].record_event(
            student_id=req.student_id,
            event_type="BOARD_EXAM_START",
            action_title=f"Started CBSE Board Exam Simulation ({sess_state.paper_title})",
            details={
                "session_id": sess_state.session_id,
                "blueprint_id": req.blueprint_id,
                "total_marks": sess_state.total_marks,
                "duration_minutes": sess_state.duration_minutes,
            },
            duration_seconds=60,
        )
        return sess_state
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start examination: {str(e)}")


@router.get("/examinations/active", response_model=Optional[ExaminationSessionState])
def get_active_examination(student_id: str = Query("STU-001")):
    """Checks if the student currently has an active in-progress examination session."""
    svcs = get_services()
    try:
        active_sess = svcs["exam_repo"].get_active_session_for_student(student_id)
        if not active_sess:
            return None
        return svcs["examination_service"].get_session_state(active_sess["session_id"], student_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Active examination check failed: {str(e)}")


@router.get("/examinations/{session_id}/state", response_model=ExaminationSessionState)
def get_examination_session_state(
    session_id: str = Path(...),
    student_id: str = Query("STU-001"),
):
    """Retrieves authoritative live state and question palette for an examination."""
    svcs = get_services()
    try:
        return svcs["examination_service"].get_session_state(session_id, student_id)
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get examination state: {str(e)}")


@router.post("/examinations/{session_id}/answer", response_model=SaveExamAnswerResponse)
def save_examination_answer(
    session_id: str = Path(...),
    req: SaveExamAnswerRequest = ...,
    student_id: str = Query("STU-001"),
):
    """
    Persists student response in real-time.
    Supports browser refresh recovery and marks question state.
    """
    svcs = get_services()
    try:
        saved = svcs["examination_service"].save_answer(
            session_id=session_id,
            student_id=student_id,
            req=req,
        )
        svcs["activity_service"].record_event(
            student_id=student_id,
            event_type="BOARD_EXAM_ANSWER_SAVE",
            action_title=f"Saved Answer for Question #{saved.question_number} (Section {saved.section_name})",
            details={
                "session_id": session_id,
                "question_id": req.question_id,
                "is_answered": saved.is_answered,
                "is_marked_for_review": saved.is_marked_for_review,
            },
            duration_seconds=req.time_spent_seconds or 20,
        )
        return saved
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save answer: {str(e)}")


@router.post("/examinations/{session_id}/submit", response_model=ExaminationResultSummary)
def submit_examination(
    session_id: str = Path(...),
    req: SubmitExamRequest = SubmitExamRequest(),
):
    """
    Finalizes examination submission.
    Evaluates responses across typologies, updates Learner Model masteries,
    classifies misconceptions, and computes section/unit analytics.
    """
    svcs = get_services()
    try:
        res_summary = svcs["examination_service"].submit_examination(
            session_id=session_id,
            student_id=req.student_id,
            is_timeout=req.is_timeout,
        )
        svcs["activity_service"].record_event(
            student_id=req.student_id,
            event_type="BOARD_EXAM_SUBMIT",
            action_title=f"Submitted CBSE Board Exam Simulation — Score: {res_summary.score_obtained}/{res_summary.total_marks} ({res_summary.percentage}%)",
            details={
                "session_id": session_id,
                "score": res_summary.score_obtained,
                "percentage": res_summary.percentage,
                "total_marks": res_summary.total_marks,
                "is_timeout": req.is_timeout,
                "weak_concepts_count": len(res_summary.weak_concepts),
            },
            duration_seconds=300,
        )
        return res_summary
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Examination submission failed: {str(e)}")


@router.get("/examinations/{session_id}/result", response_model=ExaminationResultSummary)
def get_examination_result(
    session_id: str = Path(...),
    student_id: str = Query("STU-001"),
):
    """Fetches post-submission comprehensive analytics and pedagogical feedback."""
    svcs = get_services()
    try:
        result = svcs["examination_service"].get_examination_result(session_id, student_id)
        if not result:
            raise HTTPException(status_code=404, detail=f"Result for session {session_id} not found.")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get examination result: {str(e)}")


@router.get("/student/examinations", response_model=List[ExaminationOverviewItem])
def get_student_examination_history(student_id: str = Query("STU-001")):
    """Returns past and active examination attempts for the student dashboard."""
    svcs = get_services()
    try:
        return svcs["examination_service"].get_student_examination_history(student_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch student exams: {str(e)}")


@router.get("/teacher/examinations")
def get_teacher_examinations_summary(
    role: str = Query("teacher"),
    x_role: Optional[str] = Header(None, alias="X-Role"),
):
    """Returns cohort-wide examination analytics for Teacher Dashboard."""
    svcs = get_services()
    effective_role = x_role or role
    try:
        svcs["teacher_service"]._verify_teacher_role(effective_role)
        return svcs["examination_service"].get_teacher_examinations_summary()
    except PermissionError as pe:
        raise HTTPException(status_code=403, detail=str(pe))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Teacher examinations summary error: {str(e)}")

