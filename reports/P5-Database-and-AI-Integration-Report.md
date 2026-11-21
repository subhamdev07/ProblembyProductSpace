# BodhAI (बोध AI) — P5 Database & AI Integration Report
## Schema Extensions, Dual-Database Synchronization & AI Embedding Architecture

**Project:** BodhAI (बोध AI)  
**Phase:** P5  
**Database Engines:** SQLite 3 (Local Transactional) + Supabase Cloud PostgreSQL 17.12 (`pgvector`)  
**AI Providers:** NVIDIA NIM API (Nemotron LLM & Embeddings)  
**Date:** November 21, 2026  
**Status:** COMPLETE & FULLY SYNCHRONIZED  

---

## 1. Relational Schema Architecture (P5 Extensions)

To power the authoritative CBSE Board Examination Simulation Engine, five relational tables were designed and deployed to both SQLite (`data/curriculum.db`) and Supabase Cloud PostgreSQL with foreign key enforcement:

```
+----------------------------------------------------------------------------------------------------+
|                                    P5 RELATIONAL EXAMINATION SCHEMA                                |
+----------------------------------------------------------------------------------------------------+

   +--------------------------+
   |  examination_blueprints  |
   +--------------------------+
   | blueprint_id (PK)        |
   | title                    |
   | curriculum_id (FK)       |----+ (References curricula table)
   | total_marks (80)         |    |
   | duration_minutes (180)   |    |
   | question_count (39)      |    |
   | sections_config_json     |    |
   | unit_weightage_json      |    |
   | instructions_json        |    |
   +--------------------------+    |
                | 1                |
                |                  |
                | N                |
   +--------------------------+    |
   |  examination_templates   |    |
   +--------------------------+    |
   | template_id (PK)         |    |
   | blueprint_id (FK)        |----+
   | paper_code               |
   | questions_sequence_json  |  <--- Stores exact sequence of 39 question IDs (A to E)
   | total_marks              |
   +--------------------------+
                | 1
                |
                | N
   +--------------------------+
   |   examination_sessions   |
   +--------------------------+
   | session_id (PK)          |
   | student_id (FK)          |----+ (References students table)
   | blueprint_id (FK)        |    |
   | template_id (FK)         |    |
   | status                   |    | (IN_PROGRESS, SUBMITTED, TIMED_OUT)
   | started_at, expires_at   |    | (Authoritative UTC timestamps)
   | score, percentage        |    |
   | is_timeout_submission    |    |
   +--------------------------+    |
           | 1          | 1        |
           |            |          |
           | N          | 1        |
   +-----------------------+  +-----------------------+
   |  examination_answers  |  |  examination_results  |
   +-----------------------+  +-----------------------+
   | answer_id (PK)        |  | result_id (PK)        |
   | session_id (FK)       |  | session_id (FK, UQ)   |
   | question_id (FK)      |  | score_obtained        |
   | submitted_answer_json |  | section_scores_json   |
   | is_marked_for_review  |  | unit_scores_json      |
   | is_answered           |  | chapter_scores_json   |
   | is_correct            |  | weak_concepts_json    |
   | marks_awarded         |  | strong_concepts_json  |
   | evaluation_feedback   |  | recommended_action    |
   +-----------------------+  +-----------------------+
```

### 1.1 Table Specifications
1. **`examination_blueprints`:**
   - Stores standardized board exam structures (`BP-CBSE-X-SCI-2027` and diagnostic mocks).
   - Enforces referential integrity with `curricula` via `curriculum_id`.
   - Contains serialized JSON configs for sections, cognitive distributions, and unit weightages.
2. **`examination_templates`:**
   - Pre-assembled question blueprints ensuring balanced pedagogical distribution across chemistry, biology, physics, and environmental science.
   - Guaranteed 39 questions for official CBSE simulation.
3. **`examination_sessions`:**
   - Authoritative live testing session.
   - `expires_at = started_at + timedelta(minutes=duration_minutes)` guarantees server-authoritative countdown timing independent of client device clocks.
4. **`examination_answers`:**
   - High-throughput real-time persistence table with unique constraint on `(session_id, question_id)`.
   - Allows instant question state recovery upon browser refresh.
5. **`examination_results`:**
   - Materialized performance summary storing multidimensional scores across sections, units, chapters, and cognitive levels.

---

## 2. Dual-Database Synchronization Status

| Database Layer | Active Host / File | Schema Status | Total Tables | P5 Tables Deployed |
| :--- | :--- | :--- | :---: | :---: |
| **Local Transactional** | `data/curriculum.db` (SQLite 3) | **PRAGMA foreign_keys = ON** | **31 Tables** | **All 5 Deployed** |
| **Cloud PostgreSQL** | `aws-0-ap-south-1.pooler.supabase.com:6543/postgres` | **PostgreSQL 17.12 (public)** | **31 Tables** | **All 31 Deployed** |
| **Vector Engine** | Supabase Cloud | **pgvector enabled (`vector(2048)`)** | **`curriculum_embeddings`** | **Operational** |

Both databases maintain 100% schema symmetry. Zero tables were dropped during migration.

---

## 3. AI Model & Embedding Pipeline

### 3.1 Active AI Configuration
- **LLM Provider:** NVIDIA NIM Cloud
- **Model Name:** `meta/llama-3.1-70b-instruct` / `nvidia/nemotron-4-340b-instruct`
- **Temperature:** 0.2 (High determinism for grading & rubrics)
- **Max Tokens:** 1024

### 3.2 NCERT RAG Embedding Configuration
- **Embedding Provider:** NVIDIA NIM API
- **Model:** `nvidia/nemotron-3-embed-1b`
- **Embedding Dimensions:** **2048** (Strictly enforced; no silent fallbacks)
- **Similarity Metric:** Cosine Distance (`<=>`) in Supabase pgvector
- **Textbook Grounding:** Master Class 10 Science rationalized textbook (`sources/NCERT-Class-10-Science.pdf`, 16.2 MB)
- **Fallback Resilience:** When cloud vector search is offline or throttled, BodhAI falls back seamlessly to local lexical matching without raising exceptions.

### 3.3 Multi-Typology Evaluation Logic
1. **MCQ & Assertion-Reasoning:**
   - Strict deterministic normalization: compares student's chosen option letter (`A`, `B`, `C`, `D`) with the verified answer key.
   - On mismatch: extracts question's tagged misconception pattern and routes to `MisconceptionDetectionService`.
2. **Numerical Problems:**
   - Numeric parser extracts float values from student input.
   - Evaluates within a defined $\pm 1\%$ tolerance to accommodate intermediate rounding while maintaining strict physical units.
3. **Short Answer, Long Answer & Case-Based:**
   - Rule-based keyword/key-point matching against the official CBSE rubric points.
   - Computes proportional marks according to covered scientific concepts and balanced chemical equations.

---

## 4. Security & Environment Integrity

- **Zero Credentials in Codebase:** All database passwords, pooler URLs, and NVIDIA API keys are managed exclusively via the root `.env` file.
- **Audit Verification:** Executed `scripts/audit_api_leaks.py`, scanning all source code, tests, documentation, and configuration files. Zero leaks were identified outside `.env`.
