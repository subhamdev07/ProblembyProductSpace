# P2 — Implementation Report: Question Bank & Question Generation Engine

**Project:** Adaptive Exam-Prep Tutor with a Learner Model  
**Curriculum:** CBSE Class 10 Science (Subject Code 086) — Session 2026–27  
**Phase:** P2 — Question Bank & Question Generation Engine  
**Status:** Completed & Formally Verified  
**Date:** November 2026  

---

## 1. Architectural Summary

Phase P2 establishes the assessment core of the Adaptive Exam-Prep Tutor. It integrates with P0 (Syllabus Foundation), P0.5 (AI Infrastructure), P0.6 (Environment Configuration), and P1 (Concept Graph Engine), delivering a production-grade question repository, a deterministic quality validation engine, and an AI-assisted question generation service grounded in NCERT textbook excerpts.

```
+---------------------------------------------------------------------------------+
|                                  P2 ENGINE                                      |
+---------------------------------------------------------------------------------+
|                                                                                 |
|   +-----------------------+     +-----------------------+                       |
|   | Domain Models         |     | Relational Database   |                       |
|   | (Pydantic v2)         |     | (SQLite)              |                       |
|   | - Question            |     | - questions           |                       |
|   | - Typologies (7 types)|<--->| - q_concept_mappings  |                       |
|   | - Cognitive Levels    |     | - q_lo_mappings       |                       |
|   | - Provenance          |     | - 10 B-Tree Indexes   |                       |
|   +-----------------------+     +-----------------------+                       |
|              ^                             ^                                    |
|              |                             |                                    |
|   +-----------------------------------------------------+                       |
|   | Question Repository (src/storage/question_repo.py)  |                       |
|   | - Transactional upsert, delete cascade, filtering   |                       |
|   +-----------------------------------------------------+                       |
|              ^                             ^                                    |
|              |                             |                                    |
|   +-----------------------+     +-----------------------+                       |
|   | 12-Rule Validator     |     | AI Generation Service |                       |
|   | (Deterministic QA)    |     | (NVIDIA Nemotron 30B) |                       |
|   | - Schema & Blueprint  |     | - Concept grounding   |                       |
|   | - Graph referential   |     | - Hermetic mock mode  |                       |
|   +-----------------------+     +-----------------------+                       |
|                                                                                 |
+---------------------------------------------------------------------------------+
```

---

## 2. Core Implemented Components

### 2.1 Database Schema Extensions (`src/storage/schema.sql`)
Three new tables and ten indexes were integrated into the SQLite schema:
1. `questions`: Stores core question metadata, question stem, difficulty, cognitive level, marks, timing, answer key JSON, explanation, misconception tags, and provenance JSON.
2. `question_concept_mappings`: Many-to-many junction table mapping questions to P1 concept graph nodes with foreign key cascades and primary/secondary flags.
3. `question_learning_outcome_mappings`: Junction table linking questions to CBSE Learning Outcomes.
4. Performance Indexes: Dedicated indexes on `chapter_id`, `topic_id`, `difficulty`, `cognitive_level`, `question_type`, `question_status`, and junction foreign keys.

### 2.2 Domain Models (`src/models/question.py`)
- Pydantic v2 models enforcing strict validation on question stems, answer keys, marks ($1 \le \text{marks} \le 10$), and expected duration ($10 \le \text{time} \le 900$ seconds).
- Specialized validators ensure MCQ options contain exactly 4 discrete choices and a valid correct option; Assertion-Reason choices belong to $\{A, B, C, D\}$; Numerical keys include numerical values, units, and tolerance; Short/Long Answer keys define step-by-step marking rubrics (`key_points`).

### 2.3 Repository Layer (`src/storage/question_repository.py`)
- Provides ACID transactional upsert operations that atomically update question attributes and synchronize junction table records.
- Implements rich multi-dimensional queries filtering by chapter, topic, concept, difficulty, cognitive level, typology, and moderation status.
- Aggregates comprehensive question bank statistics.

### 2.4 Deterministic Validation Service (`src/services/question_validation_service.py`)
- Implements 12 automated validation rules checking schema completeness, answer key consistency, foreign key referential integrity against the curriculum and concept graph, difficulty calibration, and duplicate detection.

### 2.5 AI-Assisted Question Generation Engine (`src/services/question_generation_service.py`)
- Integrates with the centralized `NVIDIANemotronService` (`nvidia/nemotron-3.5-lightning-30b-a3b`).
- Extracts verbatim grounding context from the target concept node's provenance records and builds a structured prompt with JSON schema constraints.
- Includes a hermetic mock generation mode to enable exhaustive automated testing without consuming live API tokens.
- Automatically routes generated questions through the 12-rule validation pipeline before assigning moderation status.

### 2.6 Seeded Chapter 1 Question Bank (`src/services/question_bank_service.py`)
- Seeds a curated set of 15 verified questions covering Chapter 1 ("Chemical Reactions and Equations"), strictly calibrated to the CBSE 2026–27 blueprint.

### 2.7 CLI Subcommands (`src/cli.py`)
Five new commands were integrated into the existing command-line interface:
- `python -m src.cli run-p2`: Executes the end-to-end P2 pipeline (seeding, validation, artifact exports).
- `python -m src.cli validate-question-bank`: Executes 12-point quality validation across all questions.
- `python -m src.cli question-stats`: Displays multi-dimensional question bank distributions.
- `python -m src.cli get-question <id>`: Fetches and displays full question details, answer key, and provenance.
- `python -m src.cli list-questions`: Lists questions with optional filters (`--chapter`, `--difficulty`, `--type`).

---

## 3. Question Bank Distribution Metrics

The initial seeded Question Bank for Chapter 1 contains 15 curated questions exhibiting the following distributions:

### 3.1 Difficulty Distribution
- **EASY:** 5 items (33.3%)
- **MEDIUM:** 5 items (33.3%)
- **HARD:** 5 items (33.3%)

### 3.2 Cognitive Level Distribution
- **KNOWLEDGE_UNDERSTANDING:** 4 items (26.7%)
- **APPLICATION:** 5 items (33.3%)
- **ANALYZE_EVALUATE_CREATE:** 6 items (40.0%)

### 3.3 Question Typology Distribution
- **MCQ (Multiple Choice):** 5 items (33.3%)
- **SHORT_ANSWER:** 3 items (20.0%)
- **ASSERTION_REASON:** 2 items (13.3%)
- **NUMERICAL:** 2 items (13.3%)
- **CASE_BASED:** 1 item (6.7%)
- **LONG_ANSWER:** 1 item (6.7%)
- **DIAGRAM_BASED:** 1 item (6.7%)

### 3.4 Concept Coverage
- **Total Concepts in Chapter 1:** 29 concepts
- **Distinct Concepts Covered:** 23 concepts (79.3% direct coverage)
- **Primary Concepts Mapped:** 15 concepts
- **Secondary / Prerequisite Concepts Mapped:** 8 concepts

---

## 4. Pipeline Execution & Data Exports

The P2 pipeline was executed via `scripts/run_p2_pipeline.py`. All artifacts were successfully exported to the `data/` directory:
- `data/question_bank_CH01.json`: Complete JSON dataset containing all 15 questions with structured answer keys, marking criteria, and provenance metadata.
- `data/question_bank_validation.json`: Formal validation log confirming 100% compliance across all 15 questions and all 12 validation rules.
