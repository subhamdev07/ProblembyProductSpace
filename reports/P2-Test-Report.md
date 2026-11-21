# P2 — Test & Quality Assurance Report

**Project:** Adaptive Exam-Prep Tutor with a Learner Model  
**Curriculum:** CBSE Class 10 Science (Subject Code 086) — Session 2026–27  
**Phase:** P2 — Question Bank & Question Generation Engine  
**Status:** Completed & Formally Verified  
**Date:** November 2026  

---

## 1. Test Architecture & Hermetic Isolation

The automated test suite for Phase P2 was designed with strict isolation guarantees:
1. **Hermetic Test Isolation:** Tests run against isolated, temporary SQLite databases created via the `temp_db` fixture and cleaned up via garbage collection upon teardown.
2. **Zero Live API Consumption:** AI question generation tests use mocked JSON candidates (`mock_response`) and `unittest.mock.MagicMock` to simulate the `NVIDIANemotronService`. Zero production tokens or API credits were consumed during testing.
3. **Multi-Phase Regression:** All existing test suites across P0 (Syllabus Foundation), P0.5 (AI Infrastructure), P0.6 (Environment Configuration), P1 (Concept Graph), and P2 (Question Bank) are executed together to guarantee zero regressions.

---

## 2. P2 Test Suite Breakdown

Phase P2 adds four dedicated test modules comprising 30 new unit and integration tests:

### 2.1 `tests/test_question_models.py` (13 Tests — 100% Passed)
- `test_question_enums`: Verifies valid string enum members for QuestionType, QuestionDifficulty, CognitiveLevel, and QuestionStatus.
- `test_question_provenance`: Verifies QuestionProvenance model instantiation and attribute access.
- `test_valid_mcq_model`: Verifies successful creation of a compliant MCQ with 4 options and valid answer key.
- `test_invalid_mcq_missing_options`: Enforces validation failure if options dict is absent.
- `test_invalid_mcq_correct_option_not_in_options`: Enforces validation failure if correct_option does not match any choice.
- `test_invalid_mcq_insufficient_options`: Rejects MCQs with fewer than 2 choices.
- `test_valid_assertion_reason_model`: Validates compliant Assertion-Reason models.
- `test_invalid_assertion_reason_option`: Rejects Assertion-Reason items where correct_option is outside $\{A, B, C, D\}$.
- `test_valid_numerical_model`: Verifies Numerical models with numerical values, units, and tolerance intervals.
- `test_invalid_numerical_missing_value`: Enforces presence of `numerical_value` in numerical keys.
- `test_valid_short_answer_model`: Verifies Short Answer models with structured `key_points`.
- `test_valid_case_based_model`: Verifies Case-Based models with stimulus passages and sub-questions.
- `test_question_constraints`: Enforces boundary constraints for marks ($1 \le m \le 10$) and expected time ($10 \le t \le 900$).

### 2.2 `tests/test_question_repository.py` (5 Tests — 100% Passed)
- `test_upsert_and_get_question`: Tests transactional SQLite insertion and full entity retrieval.
- `test_upsert_updates_existing`: Tests in-place update of question attributes and junction records.
- `test_delete_question`: Verifies cascading deletion of questions and associated junction entries.
- `test_seeded_question_bank_queries`: Verifies filtering by chapter, topic, concept, difficulty, and typology across the 15 seeded items.
- `test_question_statistics`: Verifies aggregated distribution metrics (by difficulty, cognitive level, and status).

### 2.3 `tests/test_question_validation_service.py` (8 Tests — 100% Passed)
- `test_validate_all_seeded_questions_pass`: Formally evaluates all 15 seeded Chapter 1 questions against all 12 rules (100% pass).
- `test_qv01_missing_or_short_fields`: Flags invalid ID prefixes or insufficient text lengths.
- `test_qv02_qv03_mcq_structure_checks`: Flags MCQs with fewer than 4 choices or mismatched answer keys.
- `test_qv04_invalid_chapter_or_topic`: Enforces curriculum database referential integrity.
- `test_qv05_invalid_concept_reference`: Rejects questions referencing non-existent concept nodes.
- `test_qv06_invalid_learning_outcome`: Rejects questions referencing non-existent learning outcomes.
- `test_qv09_missing_provenance_on_validated`: Enforces provenance requirements on validated questions.
- `test_qv10_duplicate_detection`: Detects duplicate question text.

### 2.4 `tests/test_question_generation_service.py` (4 Tests — 100% Passed)
- `test_generation_with_mock_response`: Validates question generation with hermetic mock JSON without live API calls.
- `test_generation_with_mocked_llm_service`: Tests generation flow with a mocked `NVIDIANemotronService`.
- `test_generation_invalid_concept_raises_error`: Enforces ValueError if target concept does not exist.
- `test_generation_without_llm_service_raises_runtime_error`: Enforces RuntimeError when LLM client is missing and live generation is attempted.

---

## 3. Full Regression Suite Results

The complete test suite was executed across the entire project:

```
============================= test session starts =============================
platform win32 -- Python 3.14.6, pytest-9.1.1, pluggy-1.6.0
rootdir: D:\Python Projects\tools\ProblemSPS
plugins: anyio-4.13.0, langsmith-0.8.15
collected 108 items

tests/test_assessment_classification.py ......                           [  5%]
tests/test_concept_extraction.py ...                                     [  8%]
tests/test_concept_graph_service.py ......                                [ 13%]
tests/test_concept_models.py .......                                     [ 20%]
tests/test_concept_repository.py .......                                 [ 26%]
tests/test_document_processor.py ....                                    [ 30%]
tests/test_hierarchy.py .......                                          [ 37%]
tests/test_idempotency.py ...                                            [ 39%]
tests/test_learning_outcomes.py ....                                     [ 43%]
tests/test_llm_service.py ........                                       [ 50%]
tests/test_models.py ........                                            [ 58%]
tests/test_ocr_service.py .......                                        [ 64%]
tests/test_question_generation_service.py ....                           [ 68%]
tests/test_question_models.py .............                              [ 80%]
tests/test_question_repository.py .....                                  [ 85%]
tests/test_question_validation_service.py ........                       [ 92%]
tests/test_security_config.py .....                                      [ 97%]
tests/test_source_management.py ...                                      [100%]

============================= 108 passed in 148.20s ============================
```

### Summary Breakdown by Phase
- **P0 Syllabus Foundation:** 36 tests passed
- **P0.5 AI Infrastructure Integration:** 18 tests passed
- **P0.6 Security & Environment Configuration:** 5 tests passed
- **P1 Concept Graph Engine:** 19 tests passed
- **P2 Question Bank & Question Generation Engine:** 30 tests passed
- **Total:** **108 passed, 0 failed, 0 skipped (100% pass rate)**

---

## 4. Secret Leakage Audit Confirmation

The automated secret auditor script (`scripts/audit_api_leaks.py`) was executed across the entire repository:

```
[AUDIT] Scanning workspace against 2 registered secret signatures...

[AUDIT PASSED] Verification Confirmed:
 -> Zero API keys or secrets found in codebase outside .env
```

Zero credentials or API keys were detected in source files, logs, or reports.
