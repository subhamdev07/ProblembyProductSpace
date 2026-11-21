# P2 — Validation Report: Question Quality & Blueprint Conformance

**Project:** Adaptive Exam-Prep Tutor with a Learner Model  
**Curriculum:** CBSE Class 10 Science (Subject Code 086) — Session 2026–27  
**Phase:** P2 — Question Bank & Question Generation Engine  
**Status:** Completed & Formally Verified  
**Date:** November 2026  

---

## 1. Quality Validation Framework (12 Deterministic Rules)

To ensure that questions generated and stored in the Question Bank adhere strictly to curriculum boundaries, scientific accuracy, and CBSE assessment standards, the `QuestionValidationService` implements a deterministic 12-point quality check:

```
+------------------------------------------------------------------------------------+
|                       12-RULE DETERMINISTIC VALIDATION PIPELINE                    |
+------------------------------------------------------------------------------------+
| QV-01: Identifier & Required Text Fields     | Validates 'Q-' prefix, stem >= 10   |
| QV-02: Typology-Specific Answer Key Schema   | Validates key structure per type    |
| QV-03: Option Cardinality & Key Match        | Enforces 4 MCQ opts & key match     |
| QV-04: Chapter & Topic Referential Integrity | Foreign keys in curriculum DB       |
| QV-05: Concept Graph Referential Integrity   | Concept IDs in P1 Concept Graph     |
| QV-06: Learning Outcome Alignment            | Outcome IDs in CBSE LO registry     |
| QV-07: Difficulty & Mark Calibration Rubric  | Validates marks & time boundaries   |
| QV-08: Cognitive Level Taxonomy Alignment    | CBSE 50/30/20 cognitive categories  |
| QV-09: Provenance Completeness               | Verifies source doc, file, page     |
| QV-10: Duplicate & Near-Duplicate Detection  | Case-normalized text deduplication  |
| QV-11: Explanation & Substantiation Rigor   | Assesses pedagogical explanation    |
| QV-12: Formative vs Summative Scope Check    | Flags excessive marks on formative  |
+------------------------------------------------------------------------------------+
```

### 1.1 Detailed Rule Specifications

1. **Rule QV-01 (Identifier & Text Completeness):** Question ID must follow deterministic format `Q-<Chapter>-<Type/Diff>-<Num>` and begin with `Q-`. Question stem and explanation must be non-empty and $\ge 10$ characters.
2. **Rule QV-02 (Typology Schema Compliance):** Answer key must contain typology-specific keys: `options` and `correct_option` for MCQ; `assertion`, `reason`, and `correct_option` for Assertion-Reason; `numerical_value` for Numerical; `key_points` list for Short/Long Answer; `passage` and `sub_questions` for Case-Based.
3. **Rule QV-03 (Option Cardinality & Integrity):** MCQs must provide exactly 4 distinct options (`A`, `B`, `C`, `D`). The specified `correct_option` must match an existing key in `options`.
4. **Rule QV-04 (Chapter & Topic Referential Integrity):** Referenced `chapter_id` and `topic_id` must exist in the P0 curriculum database.
5. **Rule QV-05 (Concept Graph Referential Integrity):** Every question must link to at least 1 concept in the P1 Concept Graph, and all referenced `concept_ids` must exist in the `concepts` table.
6. **Rule QV-06 (CBSE Learning Outcome Alignment):** All referenced `learning_outcome_ids` must exist in the `learning_outcomes` table.
7. **Rule QV-07 (Difficulty Calibration Rubric):** Easy questions cannot exceed 2 marks; Hard questions must require at least 45 seconds of cognitive effort.
8. **Rule QV-08 (Cognitive Taxonomy Classification):** `cognitive_level` must be one of the three CBSE blueprint categories: `KNOWLEDGE_UNDERSTANDING`, `APPLICATION`, or `ANALYZE_EVALUATE_CREATE`.
9. **Rule QV-09 (Source Provenance Completeness):** Any question with status `VALIDATED` must have a non-null `QuestionProvenance` containing valid `source_document_id` and `source_filename`.
10. **Rule QV-10 (Duplicate & Near-Duplicate Detection):** Cross-checks the question text against all existing repository items using normalized whitespace and lowercase matching.
11. **Rule QV-11 (Explanation & Substantiation Rigor):** Ensures that the explanation provides sufficient scientific reasoning and explicitly substantiates the designated correct answer.
12. **Rule QV-12 (Formative vs. Summative Scope Enforcement):** If a question is mapped to a formative-only curriculum topic, it cannot be assigned a high-stakes summative mark weight ($>3$ marks).

---

## 2. Chapter 1 Validation Audit Results

All 15 curated questions in the Chapter 1 Question Bank were evaluated against the 12-rule validation pipeline:

| Question ID | Typology | Difficulty | Rules Checked | Errors | Warnings | Result |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: |
| `Q-CH01-EAS-001` | MCQ | EASY | 12 | 0 | 0 | **PASSED** |
| `Q-CH01-EAS-002` | MCQ | EASY | 12 | 0 | 0 | **PASSED** |
| `Q-CH01-EAS-003` | MCQ | EASY | 12 | 0 | 0 | **PASSED** |
| `Q-CH01-EAS-004` | MCQ | EASY | 12 | 0 | 0 | **PASSED** |
| `Q-CH01-EAS-005` | MCQ | EASY | 12 | 0 | 0 | **PASSED** |
| `Q-CH01-MED-001` | SHORT_ANSWER | MEDIUM | 12 | 0 | 0 | **PASSED** |
| `Q-CH01-MED-002` | SHORT_ANSWER | MEDIUM | 12 | 0 | 0 | **PASSED** |
| `Q-CH01-MED-003` | ASSERTION_REASON | MEDIUM | 12 | 0 | 0 | **PASSED** |
| `Q-CH01-MED-004` | ASSERTION_REASON | MEDIUM | 12 | 0 | 0 | **PASSED** |
| `Q-CH01-MED-005` | NUMERICAL | MEDIUM | 12 | 0 | 0 | **PASSED** |
| `Q-CH01-HAR-001` | CASE_BASED | HARD | 12 | 0 | 0 | **PASSED** |
| `Q-CH01-HAR-002` | NUMERICAL | HARD | 12 | 0 | 0 | **PASSED** |
| `Q-CH01-HAR-003` | LONG_ANSWER | HARD | 12 | 0 | 0 | **PASSED** |
| `Q-CH01-HAR-004` | DIAGRAM_BASED | HARD | 12 | 0 | 0 | **PASSED** |
| `Q-CH01-HAR-005` | SHORT_ANSWER | HARD | 12 | 0 | 0 | **PASSED** |

---

## 3. Validation Summary Statistics

- **Total Questions Evaluated:** 15
- **Passed All 12 Rules:** 15 (100.0%)
- **Failed Questions:** 0 (0.0%)
- **Total Validation Rules Executed:** 180 checks ($15 \times 12$)
- **Validation Execution Status:** **`ALL VALID (100% COMPLIANT)`**
- **Validation Log Export:** Persisted to `data/question_bank_validation.json`
