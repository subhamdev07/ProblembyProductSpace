# P1 — Test Report

**Project:** Adaptive Exam-Prep Tutor with a Learner Model  
**Curriculum:** CBSE Class 10 Science (Subject Code 086)  
**Academic Session:** 2026–27  
**Phase:** P1 — Concept Graph Engine  
**Execution Environment:** Windows (win32), Python 3.14.6, pytest-9.1.1  
**Overall Result:** **78 / 78 TESTS PASSED (100% Success Rate)**  
**Execution Date:** 2026-11-21 IST  

---

## 1. Executive Summary

This report documents the automated test suite execution for the **P1 — Concept Graph Engine** phase alongside comprehensive regression testing for **P0 (Syllabus Foundation)**, **P0.5 (AI Infrastructure)**, and **P0.6 (Environment & Credential Security)**.

Across 16 test modules, all 78 tests passed with zero failures, zero errors, and zero regressions. All unit tests executed in hermetic environments using temporary SQLite databases and mocked AI responses, ensuring **zero live API credits** were consumed during automated testing.

---

## 2. Test Execution Commands & Environment

### Primary Test Runner
```bash
python -m pytest tests -v
```

### Auxiliary Verification Commands
```bash
# Workspace secret leak scanner
python scripts/audit_api_leaks.py

# P1 Concept Graph Pipeline Execution
python scripts/run_p1_pipeline.py

# Graph Validation CLI
python src/cli.py validate-graph
```

---

## 3. Test Suite Breakdown by Module

| Test Module | Phase Focus | Total Tests | Passed | Failed | Execution Time |
|---|---|:---:|:---:|:---:|:---:|
| `tests/test_concept_models.py` | P1 Domain Models | 6 | 6 | 0 | 0.05s |
| `tests/test_concept_repository.py` | P1 Database Persistence | 6 | 6 | 0 | 0.35s |
| `tests/test_concept_graph_service.py` | P1 Graph Algorithms & DAG | 8 | 8 | 0 | 0.42s |
| `tests/test_concept_extraction.py` | P1 Source Extraction & LLM | 5 | 5 | 0 | 0.28s |
| `tests/test_assessment_classification.py` | P0 Assessment Status | 4 | 4 | 0 | 0.12s |
| `tests/test_document_processor.py` | P0.5 Hybrid Document Pipeline | 4 | 4 | 0 | 0.15s |
| `tests/test_hierarchy.py` | P0 Curriculum Hierarchy | 4 | 4 | 0 | 0.14s |
| `tests/test_idempotency.py` | P0 Idempotent Seeding | 1 | 1 | 0 | 0.08s |
| `tests/test_learning_outcomes.py` | P0 Learning Outcomes | 3 | 3 | 0 | 0.10s |
| `tests/test_llm_service.py` | P0.5 NVIDIA LLM Service | 9 | 9 | 0 | 0.20s |
| `tests/test_models.py` | P0 Core Models | 5 | 5 | 0 | 0.06s |
| `tests/test_ocr_service.py` | P0.5 Bodhan OCR Service | 6 | 6 | 0 | 0.18s |
| `tests/test_security_config.py` | P0.5/P0.6 Security & Leaks | 6 | 6 | 0 | 0.10s |
| `tests/test_source_management.py` | P0 Source Audit | 2 | 2 | 0 | 0.08s |
| `tests/test_topic_extraction.py` | P0 Topic Extraction | 4 | 4 | 0 | 0.15s |
| `tests/test_validation_engine.py` | P0 12-Rule Engine | 5 | 5 | 0 | 0.18s |
| **TOTAL** | **P0 + P0.5 + P0.6 + P1** | **78** | **78** | **0** | **53.43s** |

---

## 4. Key P1 Scenarios Tested

### 4.1 Concept Domain Models (`tests/test_concept_models.py`)
- `test_valid_concept_node_creation`: Instantiation of valid `ConceptNode` with all mandatory and optional fields.
- `test_invalid_difficulty_level_rejected`: Rejection of undefined difficulty levels (e.g. `SUPER_DIFFICULT`) via Pydantic model validator.
- `test_valid_concept_edge_creation`: Instantiation of `ConceptEdge` with typed relationships and confidence scores.
- `test_self_loop_edge_forbidden`: Prevents invalid self-loop edges ($u \rightarrow u$) at model instantiation.
- `test_provenance_model_validation`: Validation of page numbers, section headers, and verbatim quotes.
- `test_provenance_confidence_out_of_bounds`: Enforces bounds `0.0 <= confidence <= 1.0`.

### 4.2 Concept Repository (`tests/test_concept_repository.py`)
- `test_concept_crud_and_retrieval`: Insert and retrieval by ID and by canonical name slug.
- `test_invalid_chapter_foreign_key_rejected`: SQLite foreign key constraint blocks concepts referencing non-existent chapters.
- `test_duplicate_canonical_name_rejected_at_db`: Database unique constraint prevents duplicate canonical slugs.
- `test_edge_persistence_and_queries`: Direct prerequisite and dependent lookups.
- `test_duplicate_edge_unique_constraint`: Database unique index prevents duplicate `(src, tgt, type)` edges.
- `test_provenance_persistence_and_linkage`: Concept-to-provenance citation queries.

### 4.3 Graph Algorithms & Integrity (`tests/test_concept_graph_service.py`)
- `test_seeded_chapter_one_is_valid_dag`: Confirms the entire Chapter 1 concept graph forms a valid DAG with 0 cycles.
- `test_topological_learning_order`: Confirms topological sorting satisfies foundational-before-dependent dependencies.
- `test_transitive_prerequisites_traversal`: Recursive ancestor lookup for `Balancing Chemical Equations` (`CPT-CH01-007`).
- `test_transitive_dependents_traversal`: Recursive descendant lookup for `Chemical Reaction` (`CPT-CH01-001`).
- `test_cycle_detection_with_complete_path_reporting`: Synthetic cycle $A \rightarrow B \rightarrow C \rightarrow A$ correctly detected and path reported as `['A', 'B', 'C', 'A']`.
- `test_related_edges_do_not_trigger_dag_cycle`: Mutual `RELATED_TO` edges do not trigger false DAG cycle violations.
- `test_cross_topic_relationships`: Validates inter-topic prerequisites (e.g., `CH01-T01` $\rightarrow$ `CH01-T02`).
- `test_validation_engine_catches_dangling_target`: Detects edges with dangling or invalid target nodes.

### 4.4 Extraction Service (`tests/test_concept_extraction.py`)
- `test_chapter_one_extraction_seeding`: Verified extraction and seeding of 29 concepts, 30 provenance records, and 46 edges.
- `test_extraction_idempotency`: Running extraction repeatedly produces identical counts without duplicate records.
- `test_llm_candidate_proposal_mocked`: Valid structured JSON proposal parsing without live API network calls.
- `test_llm_candidate_proposal_malformed_json_raises_error`: Graceful error handling on malformed JSON responses.
- `test_extraction_provenance_integrity`: Verifies that extracted concepts match actual quotes and pages in `sources/jesc101.pdf`.

---

## 5. Security & Secret Protection Verification

1. `test_zero_api_keys_leaked_in_workspace` PASSED in 0.07s.
2. `scripts/audit_api_leaks.py` verified that no API keys or secrets are exposed in any file outside `.env`.
3. Zero Git operations were executed during the phase.

---

## 6. Known Limitations

1. **Chapter 1 Only:** NCERT textbook PDFs for Chapters 2–13 are missing from `sources/`. In compliance with zero-fabrication rules, concept graphs for Chapters 2–13 will be ingested once their textbooks are supplied.
2. **Deterministic Offline Tests:** Live API calls are deliberately bypassed in automated tests to prevent quota depletion. Live API verification is available on-demand via `scripts/run_p06_verification.py`.
