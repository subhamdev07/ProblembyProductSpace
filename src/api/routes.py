"""
BodhAI REST API Routes
Implements all student diagnostic assessment, learner mastery, targeted remediation,
spaced repetition, teacher dashboard, and NCERT RAG search endpoints.
"""

from typing import Optional, Dict, Any, List
from fastapi import APIRouter, HTTPException, Query, Path, Header
from pydantic import BaseModel, Field

from src.storage.database import Database
from src.storage.question_repository import QuestionRepository
from src.storage.assessment_repository import AssessmentRepository
from src.storage.learner_repository import LearnerRepository
from src.storage.concept_repository import ConceptRepository
from src.storage.remediation_repository import RemediationRepository

from src.services.answer_evaluation_service import AnswerEvaluationService
from src.services.learner_model_service import LearnerModelService
from src.services.adaptive_selection_service import AdaptiveQuestionSelectionService
from src.services.diagnostic_assessment_service import DiagnosticAssessmentService
from src.services.misconception_detection_service import MisconceptionDetectionService
from src.services.spaced_repetition_service import SpacedRepetitionService
from src.services.targeted_remediation_service import TargetedRemediationService
from src.services.rag_service import RAGService
from src.services.teacher_dashboard_service import TeacherDashboardService

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

router = APIRouter(prefix="/api")

# Lazy-loaded / singleton dependencies
_db: Optional[Database] = None
_question_repo: Optional[QuestionRepository] = None
_assessment_repo: Optional[AssessmentRepository] = None
_learner_repo: Optional[LearnerRepository] = None
_concept_repo: Optional[ConceptRepository] = None
_remediation_repo: Optional[RemediationRepository] = None

_evaluation_service: Optional[AnswerEvaluationService] = None
_learner_service: Optional[LearnerModelService] = None
_adaptive_service: Optional[AdaptiveQuestionSelectionService] = None
_misconception_service: Optional[MisconceptionDetectionService] = None
_spaced_repetition_service: Optional[SpacedRepetitionService] = None
_targeted_remediation_service: Optional[TargetedRemediationService] = None
_rag_service: Optional[RAGService] = None
_teacher_service: Optional[TeacherDashboardService] = None
_diagnostic_service: Optional[DiagnosticAssessmentService] = None


def get_services(db_path: str = "data/curriculum.db"):
    global _db, _question_repo, _assessment_repo, _learner_repo, _concept_repo, _remediation_repo
    global _evaluation_service, _learner_service, _adaptive_service, _diagnostic_service
    global _misconception_service, _spaced_repetition_service, _targeted_remediation_service
    global _rag_service, _teacher_service

    if _db is None:
        _db = Database(db_path)
        _question_repo = QuestionRepository(_db)
        _assessment_repo = AssessmentRepository(_db)
        _learner_repo = LearnerRepository(_db)
        _concept_repo = ConceptRepository(_db)
        _remediation_repo = RemediationRepository(_db)

        # Ensure demo cohort students exist
        _learner_repo.get_or_create_student("STU-001", "Aarav Sharma", 10)
        _learner_repo.get_or_create_student("STU-002", "Priya Patel", 10)
        _learner_repo.get_or_create_student("STU-003", "Rohan Verma", 10)

        _evaluation_service = AnswerEvaluationService()
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

    return {
        "db": _db,
        "question_repo": _question_repo,
        "assessment_repo": _assessment_repo,
        "learner_repo": _learner_repo,
        "concept_repo": _concept_repo,
        "remediation_repo": _remediation_repo,
        "evaluation_service": _evaluation_service,
        "learner_service": _learner_service,
        "adaptive_service": _adaptive_service,
        "misconception_service": _misconception_service,
        "spaced_repetition_service": _spaced_repetition_service,
        "targeted_remediation_service": _targeted_remediation_service,
        "rag_service": _rag_service,
        "teacher_service": _teacher_service,
        "diagnostic_service": _diagnostic_service,
    }


class StartAssessmentRequest(BaseModel):
    student_id: str = Field(default="STU-001")
    chapter_id: str = Field(default="CH-01")
    question_count: int = Field(default=5, ge=1, le=15)


class FinalizeAssessmentRequest(BaseModel):
    student_id: str = Field(default="STU-001")


# ------------------------------------------------------------------------------
# Health Check
# ------------------------------------------------------------------------------
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


# ------------------------------------------------------------------------------
# Student Dashboard
# ------------------------------------------------------------------------------
@router.get("/student/dashboard", response_model=StudentDashboardData)
def get_student_dashboard(student_id: str = Query("STU-001")):
    svcs = get_services()
    try:
        return svcs["learner_service"].get_student_dashboard(student_id=student_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch dashboard: {str(e)}")


# ------------------------------------------------------------------------------
# Assessment Operations
# ------------------------------------------------------------------------------
@router.post("/assessments/start", response_model=AssessmentSession)
def start_assessment(payload: StartAssessmentRequest):
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
        return summary
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Finalization error: {str(e)}")


# ------------------------------------------------------------------------------
# Learner Concept Mastery & History
# ------------------------------------------------------------------------------
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


# ------------------------------------------------------------------------------
# Adaptive Question Selection
# ------------------------------------------------------------------------------
@router.get("/questions/next", response_model=AdaptiveQuestionRecommendation)
def get_next_question(
    student_id: str = Query("STU-001"),
    chapter_id: str = Query("CH-01"),
    exclude: Optional[str] = Query(None, description="Comma-separated question IDs to exclude"),
):
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


# ------------------------------------------------------------------------------
# P4: Evidence-Based Misconception Detection Endpoints
# ------------------------------------------------------------------------------
@router.get("/student/misconceptions", response_model=List[StudentMisconceptionItem])
def get_student_misconceptions(
    student_id: str = Query("STU-001"), status: Optional[str] = Query(None)
):
    svcs = get_services()
    return svcs["misconception_service"].get_student_misconceptions(student_id, status)


@router.get("/student/misconceptions/summary")
def get_misconceptions_summary():
    svcs = get_services()
    return svcs["misconception_service"].get_misconception_summary_by_cohort()


# ------------------------------------------------------------------------------
# P4: Targeted Remediation Endpoints
# ------------------------------------------------------------------------------
@router.get("/student/remediation", response_model=TargetedRemediationPayload)
def get_remediation_package(
    student_id: str = Query("STU-001"), concept_id: Optional[str] = Query(None)
):
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
        return svcs["targeted_remediation_service"].complete_remediation_practice(
            remediation_id=payload.remediation_id,
            student_id=payload.student_id,
            question_id=payload.question_id,
            student_answer=payload.student_answer,
        )
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to complete remediation: {str(e)}")


# ------------------------------------------------------------------------------
# P4: Spaced Repetition Endpoints
# ------------------------------------------------------------------------------
@router.get("/student/revision-due", response_model=List[SpacedRepetitionItem])
def get_due_revisions(student_id: str = Query("STU-001")):
    svcs = get_services()
    # Sync any un-scheduled assessed concepts first
    svcs["spaced_repetition_service"].sync_weak_concepts_to_schedule(student_id)
    return svcs["spaced_repetition_service"].get_due_revisions(student_id)


@router.get("/student/revision-upcoming", response_model=List[SpacedRepetitionItem])
def get_upcoming_revisions(student_id: str = Query("STU-001")):
    svcs = get_services()
    svcs["spaced_repetition_service"].sync_weak_concepts_to_schedule(student_id)
    return svcs["spaced_repetition_service"].get_upcoming_revisions(student_id)


@router.post("/student/revision/complete", response_model=CompleteRevisionResponse)
def complete_revision(payload: CompleteRevisionRequest):
    svcs = get_services()
    try:
        return svcs["spaced_repetition_service"].complete_revision(
            student_id=payload.student_id,
            concept_id=payload.concept_id,
            is_correct=payload.is_correct,
            difficulty_rating=payload.difficulty_rating or "NORMAL",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to complete revision: {str(e)}")


# ------------------------------------------------------------------------------
# P4: Teacher Dashboard Endpoints
# ------------------------------------------------------------------------------
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


# ------------------------------------------------------------------------------
# P4: NCERT RAG Retrieval Endpoints
# ------------------------------------------------------------------------------
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
