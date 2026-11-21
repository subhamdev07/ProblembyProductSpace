"""
P2 — Question Bank & Question Generation Engine Pipeline Runner
Executes:
1. Database schema initialization / check
2. Chapter 1 question bank seeding (15 curated, source-grounded questions)
3. 12-rule Question Quality Validation
4. Export of canonical Question Bank JSON artifacts to data/
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.storage.database import Database, CurriculumRepository
from src.storage.concept_repository import ConceptRepository
from src.storage.question_repository import QuestionRepository
from src.services.question_validation_service import QuestionValidationService
from src.services.question_bank_service import QuestionBankService


def run_p2_pipeline(db_path: str = "data/curriculum.db") -> Dict[str, Any]:
    print("=" * 60)
    print("P2 — QUESTION BANK & GENERATION ENGINE PIPELINE")
    print("CBSE Class 10 Science (086) - Session 2026-27")
    print("=" * 60)

    # 1. Connect to Database
    print("\n[Step 1/4] Connecting to relational curriculum database...")
    db = Database(db_path)
    curr_repo = CurriculumRepository(db)
    concept_repo = ConceptRepository(db)
    q_repo = QuestionRepository(db)
    print(f" Database connected at: {db_path}")

    # 2. Seed Chapter 1 Question Bank
    print("\n[Step 2/4] Seeding Chapter 1 Question Bank (15 curated items)...")
    val_service = QuestionValidationService(q_repo, concept_repo, curr_repo)
    qb_service = QuestionBankService(q_repo, val_service)
    seed_result = qb_service.seed_chapter_one_question_bank()

    print(f" Seeded: {seed_result['questions_seeded']} Questions")
    print(f" Validated: {seed_result['questions_validated']} Questions")
    print(f" Difficulty Breakdown: {seed_result['statistics']['by_difficulty']}")
    print(f" Cognitive Level Breakdown: {seed_result['statistics']['by_cognitive_level']}")
    print(f" Question Types: {seed_result['statistics']['by_question_type']}")

    # 3. Comprehensive 12-Rule Quality Validation
    print("\n[Step 3/4] Executing 12-rule Question Bank Validation Engine...")
    summary = val_service.validate_all_questions()

    print(f" Total Evaluated: {summary.total_evaluated}")
    print(f" Valid Count: {summary.valid_count}")
    print(f" Invalid Count: {summary.invalid_count}")
    print(f" Overall Status: {'ALL PASSED' if summary.all_valid else 'VALIDATION FAILURES DETECTED'}")
    if summary.errors_by_rule:
        print(f" Errors by Rule: {summary.errors_by_rule}")

    # 4. Export Machine-Readable Artifacts
    print("\n[Step 4/4] Exporting machine-readable Question Bank JSON artifacts...")
    os.makedirs("data", exist_ok=True)

    all_questions = q_repo.get_all_questions()
    qb_export = {
        "chapter_id": "CH-01",
        "total_questions": len(all_questions),
        "statistics": seed_result["statistics"],
        "questions": [q.model_dump() for q in all_questions],
    }
    qb_path = "data/question_bank_CH01.json"
    with open(qb_path, "w", encoding="utf-8") as f:
        json.dump(qb_export, f, indent=2, ensure_ascii=False)
    print(f" Exported Chapter 1 Question Bank to: {qb_path}")

    val_export = {
        "total_evaluated": summary.total_evaluated,
        "valid_count": summary.valid_count,
        "invalid_count": summary.invalid_count,
        "all_valid": summary.all_valid,
        "errors_by_rule": summary.errors_by_rule,
        "detailed_results": {qid: res.model_dump() for qid, res in summary.question_results.items()},
    }
    val_path = "data/question_bank_validation.json"
    with open(val_path, "w", encoding="utf-8") as f:
        json.dump(val_export, f, indent=2, ensure_ascii=False)
    print(f" Exported Question Bank validation results to: {val_path}")

    print("\n" + "=" * 60)
    print("P2 PIPELINE COMPLETED SUCCESSFULLY!")
    print("=" * 60)

    return {
        "status": "SUCCESS",
        "total_questions": len(all_questions),
        "all_valid": summary.all_valid,
        "statistics": seed_result["statistics"],
    }


if __name__ == "__main__":
    run_p2_pipeline()
