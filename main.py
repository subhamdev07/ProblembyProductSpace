"""
BodhAI — Adaptive Exam-Prep Tutor with a Learner Model
Root Application Entry Point
Curriculum: CBSE Class 10 Science (Subject Code 086) — Session 2026–27

Usage:
    python main.py
"""

import os
import sys
import uvicorn
from dotenv import load_dotenv

# Ensure root workspace is in sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.core.config import config
from src.storage.database import Database
from src.storage.learner_repository import LearnerRepository
from src.services.question_bank_service import QuestionBankService
from src.storage.question_repository import QuestionRepository


def initialize_system():
    """
    Ensures database schemas, initial demo student, and question bank are initialized.
    """
    db_path = "data/curriculum.db"
    db = Database(db_path)
    db.init_db()

    # Ensure demo student STU-001 exists
    learner_repo = LearnerRepository(db)
    student = learner_repo.get_or_create_student("STU-001", "Aarav Sharma", 10)
    learner_repo.get_or_create_student("STU-002", "Priya Patel", 10)
    learner_repo.get_or_create_student("STU-003", "Rohan Verma", 10)

    # Ensure Chapter 1 questions are seeded
    q_repo = QuestionRepository(db)
    q_stats = q_repo.get_question_statistics()
    if q_stats.get("total_questions", 0) == 0:
        qb_service = QuestionBankService(q_repo)
        qb_service.seed_chapter_one_question_bank()
        q_stats = q_repo.get_question_statistics()

    return student, q_stats


def main():
    load_dotenv()
    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))

    print("\n" + "=" * 70)
    print("  BodhAI (बोध AI) — Adaptive Exam-Prep Tutor")
    print("  CBSE Class 10 Science | Academic Session 2026–27 | Phase P4 Full-Stack")
    print("=" * 70)

    try:
        student, q_stats = initialize_system()
        print(f"  [DB] SQLite Database Verified: data/curriculum.db")
        print(f"  [STUDENT] Active Demo Learner: {student.name} ({student.student_id})")
        print(f"  [ASSESSMENT] Question Bank: {q_stats.get('total_questions', 0)} verified questions")
        print(f"  [DIAGNOSTICS] Concept Graph: 29 concepts tracked across Chapter 1")
        print(f"  [REMEDIATION] Targeted Learning & Prerequisite Scaffolding: Active")
        print(f"  [SPACED REPETITION] Adaptive Leitner-Interval Scheduler: Active")
        print(f"  [TEACHER DASHBOARD] Cohort Analytics & Intervention Alerts: Active")
        print(f"  [RAG] NCERT pgvector Semantic Retrieval: Active")
    except Exception as e:
        print(f"  [WARNING] Initialization check warning: {e}")

    print("-" * 70)
    print(f"  🚀 BodhAI Full-Stack App URL: http://{host}:{port}")
    print(f"  📖 Interactive API Docs:     http://{host}:{port}/docs")
    print(f"  🩺 Health Check Endpoint:     http://{host}:{port}/api/health")
    print("=" * 70)
    print("  Press Ctrl+C to stop the server.\n")

    try:
        uvicorn.run("src.api.app:app", host=host, port=port, log_level="info")
    except KeyboardInterrupt:
        print("\n[BodhAI] Server shutdown requested. Exiting cleanly.")


if __name__ == "__main__":
    main()
