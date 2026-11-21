"""
P1 — Concept Graph Engine Pipeline Runner
Executes:
1. Database schema initialization / check
2. Chapter 1 source-grounded concept extraction & seeding
3. 8-rule graph validation (DAG, referential integrity, cycle detection)
4. Export of canonical concept graph JSON artifacts to data/
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.storage.database import Database, CurriculumRepository
from src.storage.concept_repository import ConceptRepository
from src.services.concept_extraction_service import ConceptExtractionService
from src.services.concept_graph_service import ConceptGraphService


def run_p1_pipeline(db_path: str = "data/curriculum.db") -> Dict[str, Any]:
    print("=" * 60)
    print("P1 — CONCEPT GRAPH ENGINE PIPELINE EXECUTION")
    print("CBSE Class 10 Science (086) - Session 2026-27")
    print("=" * 60)

    # 1. Initialize Storage
    print("\n[Step 1/4] Connecting to relational curriculum database...")
    db = Database(db_path)
    curr_repo = CurriculumRepository(db)
    concept_repo = ConceptRepository(db)
    print(f" Database connected at: {db_path}")

    # 2. Extract & Seed Chapter 1
    print("\n[Step 2/4] Extracting & seeding Chapter 1 source-grounded concept graph...")
    extractor = ConceptExtractionService(concept_repo)
    seed_result = extractor.extract_and_seed_chapter_one()
    print(f" Seeded {seed_result['concepts_seeded']} Concepts, "
          f"{seed_result['provenance_records_seeded']} Provenance citations, "
          f"{seed_result['edges_seeded']} Relationship edges.")

    # 3. Validate Graph (DAG, Cycles, Integrity)
    print("\n[Step 3/4] Executing 8-rule Graph Validation Engine...")
    graph_service = ConceptGraphService(concept_repo, curr_repo)
    val_result = graph_service.validate_graph()

    print(f" Graph Validation: {'PASSED (0 Errors)' if val_result.is_valid else 'FAILED'}")
    print(f" DAG Verification: {'PASSED (Acyclic)' if val_result.is_dag else 'FAILED (Cycle Detected)'}")
    if val_result.cycle_detected:
        print(f" Cycle Path: {' -> '.join(val_result.cycle_path or [])}")
    print(f" Rules Evaluated: {val_result.rules_evaluated}")
    print(f" Errors: {len(val_result.errors)} | Warnings: {len(val_result.warnings)}")

    # 4. Export Artifacts
    print("\n[Step 4/4] Exporting machine-readable Concept Graph JSON artifacts...")
    os.makedirs("data", exist_ok=True)

    # Export Chapter 1 Graph
    ch01_graph = graph_service.get_chapter_graph("CH-01")
    ch01_path = "data/concept_graph_CH01.json"
    with open(ch01_path, "w", encoding="utf-8") as f:
        json.dump(ch01_graph, f, indent=2, ensure_ascii=False)
    print(f" Exported Chapter 1 graph to: {ch01_path}")

    # Export Validation Results
    val_path = "data/concept_graph_validation.json"
    with open(val_path, "w", encoding="utf-8") as f:
        json.dump(val_result.model_dump(), f, indent=2, ensure_ascii=False)
    print(f" Exported graph validation results to: {val_path}")

    print("\n" + "=" * 60)
    print("P1 PIPELINE COMPLETED SUCCESSFULLY!")
    print("=" * 60)

    return {
        "status": "SUCCESS",
        "is_valid": val_result.is_valid,
        "is_dag": val_result.is_dag,
        "total_concepts": val_result.statistics.get("total_concepts", 0),
        "total_edges": val_result.statistics.get("total_edges", 0),
        "total_provenance": val_result.statistics.get("total_provenance_records", 0),
        "statistics": val_result.statistics,
    }


if __name__ == "__main__":
    run_p1_pipeline()
