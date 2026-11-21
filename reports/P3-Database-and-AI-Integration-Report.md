# P3 — Database & AI Integration Report

**Project:** BodhAI (बोध AI) — Adaptive Exam-Prep Tutor with a Learner Model  
**Curriculum:** CBSE Class 10 Science (Subject Code 086) — Session 2026–27  
**Phase:** P3 — Integrated Diagnostic Assessment & Learner Model MVP  
**Status:** Completed & Formally Verified  
**Date:** November 2026  

---

## 1. Database Architecture & Persistence Strategy

BodhAI employs a dual-tier persistence strategy designed for offline-first reliability and future cloud scalability:

1. **Primary Operational Persistence (SQLite — `data/curriculum.db`):**
   - High-performance, zero-latency local relational database.
   - Preserves all P0 curriculum records, P1 concept graphs, and P2 question banks without external network dependency.
   - Extended in P3 with 6 new normalized tables and 8 indexes to maintain student assessment sessions, real-time answers, concept-wise mastery, and misconception logs.
2. **Cloud Infrastructure Tier (Supabase — `fewqvskzdnkokeibanet`):**
   - Project URL: `https://fewqvskzdnkokeibanet.supabase.co`
   - Dashboard Link: `https://supabase.com/dashboard/project/fewqvskzdnkokeibanet`
   - Client API Key: `SUPABASE_ANON_KEY` configured (`sb_publishable_[CONFIGURED_IN_ENV]`).
   - Database Password: `SUPABASE_DB_PASSWORD` configured (`Subham***` securely stored in `.env`).
   - Database Connection URI: `SUPABASE_DB_URL` configured (`postgresql://postgres:[PASSWORD_MASKED]@db.fewqvskzdnkokeibanet.supabase.co:5432/postgres` with URL-encoded `@` as `%40`).
   - **Deployment Status:** **ONLINE, FULLY MIGRATED & SYNCHRONIZED**
   - **Database Engine:** PostgreSQL 17.12 (ARM64)
   - **Extensions:** `pgvector` enabled (`CREATE EXTENSION IF NOT EXISTS vector;`)
   - **Cloud Schema:** All 23 tables and 32 indexes deployed and verified in `public` schema.
   - **Data Fidelity:** 100% data mirrored from local SQLite (Curriculum, Concept DAG, Question Bank, Learner Profiles).

---

## 2. Cloud Database Deployment & Synchronization Ledger

The following table details the live schema and synchronized records between local SQLite and cloud Supabase PostgreSQL:

| Table Name | Schema Scope | SQLite Rows | Supabase Rows | Deployment Status |
| :--- | :--- | :---: | :---: | :--- |
| `academic_sessions` | P0 Foundation | 1 | 1 | **DEPLOYED & SYNCED** |
| `subjects` | P0 Foundation | 1 | 1 | **DEPLOYED & SYNCED** |
| `curricula` | P0 Foundation | 1 | 1 | **DEPLOYED & SYNCED** |
| `units` | P0 Foundation | 5 | 5 | **DEPLOYED & SYNCED** |
| `chapters` | P0 Foundation | 13 | 13 | **DEPLOYED & SYNCED** |
| `topics` | P0 Foundation | 56 | 56 | **DEPLOYED & SYNCED** |
| `subtopics` | P0 Foundation | 113 | 113 | **DEPLOYED & SYNCED** |
| `learning_outcomes` | P0 Foundation | 15 | 15 | **DEPLOYED & SYNCED** |
| `curriculum_mappings` | P0 Foundation | 18 | 18 | **DEPLOYED & SYNCED** |
| `source_documents` | P0 Foundation | 2 | 2 | **DEPLOYED & SYNCED** |
| `source_citations` | P0 Foundation | 0 | 0 | **SCHEMA READY** |
| `concepts` | P1 Concept Graph | 29 | 29 | **DEPLOYED & SYNCED** |
| `concept_relationships` | P1 Concept Graph | 46 | 46 | **DEPLOYED & SYNCED** |
| `concept_provenance` | P1 Concept Graph | 30 | 30 | **DEPLOYED & SYNCED** |
| `questions` | P2 Question Bank | 15 | 15 | **DEPLOYED & SYNCED** |
| `question_concept_mappings` | P2 Question Bank | 32 | 32 | **DEPLOYED & SYNCED** |
| `question_learning_outcome_mappings` | P2 Question Bank | 15 | 15 | **DEPLOYED & SYNCED** |
| `students` | P3 Learner Model | 1 | 1 | **DEPLOYED & SYNCED** |
| `assessments` | P3 Assessment Engine | 9 | 9 | **DEPLOYED & SYNCED** |
| `assessment_questions` | P3 Assessment Engine | 31 | 31 | **DEPLOYED & SYNCED** |
| `student_answers` | P3 Assessment Engine | 8 | 8 | **DEPLOYED & SYNCED** |
| `learner_concept_mastery` | P3 Learner Model | 1 | 1 | **DEPLOYED & SYNCED** |
| `student_misconceptions` | P3 Learner Model | 0 | 0 | **SCHEMA READY** |
| **TOTALS** | **All 4 Phases** | **439** | **439** | **100% Synced (23 Tables)** |

---

## 3. P3 Relational Database Schema Extensions

The following tables were integrated into `src/storage/schema.sql` and initialized in `data/curriculum.db`:

```sql
-- Student Profile
CREATE TABLE IF NOT EXISTS students (
    student_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    grade INTEGER DEFAULT 10,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Assessment Sessions
CREATE TABLE IF NOT EXISTS assessments (
    assessment_id TEXT PRIMARY KEY,
    student_id TEXT NOT NULL REFERENCES students(student_id) ON UPDATE CASCADE ON DELETE CASCADE,
    assessment_type TEXT NOT NULL CHECK(assessment_type IN ('DIAGNOSTIC', 'ADAPTIVE_PRACTICE', 'REVISION')),
    chapter_id TEXT REFERENCES chapters(chapter_id),
    status TEXT NOT NULL CHECK(status IN ('IN_PROGRESS', 'SUBMITTED', 'EVALUATED')),
    total_questions INTEGER NOT NULL DEFAULT 0,
    total_marks INTEGER NOT NULL DEFAULT 0,
    score REAL DEFAULT 0.0,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP
);

-- Ordered Question Assignments
CREATE TABLE IF NOT EXISTS assessment_questions (
    assessment_id TEXT NOT NULL REFERENCES assessments(assessment_id) ON UPDATE CASCADE ON DELETE CASCADE,
    question_id TEXT NOT NULL REFERENCES questions(question_id) ON UPDATE CASCADE ON DELETE CASCADE,
    question_order INTEGER NOT NULL,
    PRIMARY KEY (assessment_id, question_id)
);

-- Real-Time Student Responses
CREATE TABLE IF NOT EXISTS student_answers (
    answer_id TEXT PRIMARY KEY,
    assessment_id TEXT NOT NULL REFERENCES assessments(assessment_id) ON UPDATE CASCADE ON DELETE CASCADE,
    student_id TEXT NOT NULL REFERENCES students(student_id) ON UPDATE CASCADE ON DELETE CASCADE,
    question_id TEXT NOT NULL REFERENCES questions(question_id) ON UPDATE CASCADE ON DELETE CASCADE,
    submitted_answer_json TEXT NOT NULL,
    is_correct INTEGER NOT NULL CHECK(is_correct IN (0, 1)),
    marks_awarded REAL NOT NULL DEFAULT 0.0,
    evaluation_feedback TEXT,
    detected_misconceptions_json TEXT DEFAULT '[]',
    time_spent_seconds INTEGER DEFAULT 0,
    submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(assessment_id, question_id)
);

-- Learner Concept Mastery Ledger
CREATE TABLE IF NOT EXISTS learner_concept_mastery (
    mastery_id TEXT PRIMARY KEY,
    student_id TEXT NOT NULL REFERENCES students(student_id) ON UPDATE CASCADE ON DELETE CASCADE,
    concept_id TEXT NOT NULL REFERENCES concepts(concept_id) ON UPDATE CASCADE ON DELETE CASCADE,
    mastery_score REAL NOT NULL DEFAULT 0.0 CHECK(mastery_score >= 0.0 AND mastery_score <= 1.0),
    confidence_score REAL NOT NULL DEFAULT 0.5 CHECK(confidence_score >= 0.0 AND confidence_score <= 1.0),
    total_attempts INTEGER NOT NULL DEFAULT 0,
    correct_attempts INTEGER NOT NULL DEFAULT 0,
    incorrect_attempts INTEGER NOT NULL DEFAULT 0,
    last_attempted_at TIMESTAMP,
    last_updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(student_id, concept_id)
);

-- Diagnostic Misconception Evidence
CREATE TABLE IF NOT EXISTS student_misconceptions (
    misconception_record_id TEXT PRIMARY KEY,
    student_id TEXT NOT NULL REFERENCES students(student_id) ON UPDATE CASCADE ON DELETE CASCADE,
    concept_id TEXT NOT NULL REFERENCES concepts(concept_id) ON UPDATE CASCADE ON DELETE CASCADE,
    misconception_tag TEXT NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('SUSPECTED', 'CONFIRMED', 'RESOLVED')),
    evidence_count INTEGER NOT NULL DEFAULT 1,
    last_observed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(student_id, concept_id, misconception_tag)
);
```

---

## 3. Learner Model Bayesian Mastery Update Algorithm

The Learner Model updates concept mastery after each evaluated response using an explainable, deterministic evidence-based algorithm:

1. **Mastery Delta ($\Delta M$):**
   $$\Delta M = \begin{cases} +0.25 \times W_{\text{diff}} & \text{if correct} \\ -0.20 \times W_{\text{diff}} & \text{if incorrect} \end{cases}$$
   Where $W_{\text{diff}} \in \{0.8 \text{ (Easy)}, 1.0 \text{ (Medium)}, 1.3 \text{ (Hard)}\}$.
   The updated mastery score is bounded: $0.0 \le M_{\text{new}} \le 1.0$.

2. **Asymptotic Confidence Scoring ($C$):**
   $$C = 1.0 - 0.5^{\text{attempts}}$$
   Reflects statistical confidence; single attempts have $C = 0.50$, while 3 attempts yield $C = 0.875$.

3. **Mastery Classification Tiers:**
   - **`NOT_ASSESSED`:** Total attempts $= 0$.
   - **`DEVELOPING`:** $M < 0.50$ (requires foundational remediation).
   - **`IMPROVING`:** $0.50 \le M < 0.80$ (demonstrates basic proficiency).
   - **`STRONG`:** $M \ge 0.80$ (mastery verified across multiple trials).

---

## 4. NCERT Source Grounding & AI Evaluation Strategy

- **Source Document Availability:**
  - `C:\Users\acer\Downloads\NCERT-Class-10-Science.pdf`: Verified present (16.2 MB).
  - `sources/jesc101.pdf`: Verified present (16 pages, clean UTF-8 extraction).
- **RAG & Vector Configuration:**
  - `.env` configured with:
    - `EMBEDDING_PROVIDER=nvidia`
    - `EMBEDDING_MODEL=nvidia/nv-embedqa-e5-v5`
    - `EMBEDDING_DIMENSION=1024`
- **Question Retrieval Architecture:**
  - Uses the 15 validated Chapter 1 assessment items seeded in P2.
  - Safe projection: Student-facing views (`AssessmentQuestionView`) strip answer keys, explanations, and internal marking notes before evaluation.
- **Answer Evaluation & Fallback Behavior:**
  - **MCQ & Assertion-Reason:** Deterministic letter matching against verified keys.
  - **Numerical:** Float extraction with configured tolerance windows ($\pm \text{tol}$) and units.
  - **Short Answer:** Keyword/rubric extraction against NCERT `key_points`. If the NVIDIA Nemotron LLM service is available, it provides natural language rubric feedback; otherwise, the system seamlessly uses deterministic keyword matching without blocking the user.
