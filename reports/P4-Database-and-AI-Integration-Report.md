# BodhAI (बोध AI) — P4 Database & AI Integration Report
## Supabase Cloud, pgvector Indexing & NVIDIA AI Model Integration

**Project:** BodhAI (बोध AI) — Adaptive Exam-Prep Tutor with a Learner Model  
**Curriculum:** CBSE Class 10 Science (Subject Code 086), Academic Session 2026–27  
**Database:** Dual-Engine Architecture (Local SQLite `data/curriculum.db` + Supabase Cloud PostgreSQL 17.12)  
**Vector Engine:** PostgreSQL `pgvector` with 2048-dimensional dense embeddings  
**AI Embeddings:** Live NVIDIA Nemotron Embeddings (`nvidia/nemotron-3-embed-1b`)  
**Phase:** P4 — Full-Stack Implementation  
**Execution Date:** November 21, 2026

---

## 1. Executive Summary

Phase P4 verified, extended, and stabilized the cloud persistence and semantic AI retrieval infrastructure for BodhAI. The application leverages a dual-engine architecture:
- **Local SQLite Engine (`data/curriculum.db`)**: Provides zero-latency, local-first transactional storage for offline-first development, automated tests, and immediate UI reactivity.
- **Supabase Cloud Engine (PostgreSQL 17.12 + pgvector + Storage)**: Provides enterprise cloud persistence, vector similarity search for NCERT textbook RAG, and cloud asset storage.

All 26 database tables, the `pgvector` extension, the private `curriculum-sources` storage bucket, and live vector indexing were deployed, validated, and verified.

---

## 2. Supabase Cloud Configuration & Connection Verification

The Supabase Cloud connection was established directly using authenticated PostgreSQL connection pooling.

### 2.1 Connection Verification Details
- **Project Ref**: `fewqvskzdnkokeibanet`
- **PostgreSQL Version**: `PostgreSQL 17.12 on aarch64-unknown-linux-gnu, compiled by gcc (Ubuntu 11.4.0) 11.4.0, 64-bit`
- **Host**: `aws-0-ap-south-1.pooler.supabase.com` (Port 5432)
- **Database**: `postgres`
- **SSL Mode**: `require`
- **pgvector Extension**: Installed and verified via `CREATE EXTENSION IF NOT EXISTS vector;`

---

## 3. Database Schema Deployment: 26 Unified Tables

The public schema on Supabase Cloud and the local SQLite database share identical relational definitions across all 26 tables:

### A. Curriculum Foundation (11 Tables)
1. `academic_sessions`: Academic session tracking (`SESS-2026-27`).
2. `subjects`: CBSE subject records (`SUBJ-SCI-10`, Code 086).
3. `curricula`: Official curriculum specification.
4. `units`: 5 official CBSE units (I to V).
5. `chapters`: 13 official CBSE chapters (marked SUMMATIVE).
6. `topics`: 56 syllabus-aligned topics.
7. `subtopics`: 113 granular subtopics.
8. `learning_outcomes`: 15 official CBSE learning outcomes.
9. `textbook_references`: NCERT Class 10 textbook provenance records.
10. `curriculum_audit_log`: System change logging.
11. `source_documents`: Verified syllabus and textbook PDF records.

### B. Concept Graph DAG (3 Tables)
12. `concepts`: 29 atomic concepts for Chapter 1 with canonical slugs, hierarchy, and Bloom's classification.
13. `concept_relationships`: 34 directed pedagogical edges (`PREREQUISITE_OF`, `EXTENDS`, `ANALOGOUS_TO`, `CORRELATED_WITH`).
14. `concept_learning_outcomes`: Concept-to-CBSE LO mappings.

### C. Question Bank & Generation (3 Tables)
15. `questions`: Validated assessment questions across 7 CBSE typologies.
16. `question_concept_mappings`: Multi-concept indexing per question.
17. `question_learning_outcome_mappings`: CBSE LO tracking per question.

### D. Assessment & Learner Model (6 Tables)
18. `students`: Learner profiles (e.g. `STU-001 Aarav Sharma`, `STU-002 Priya Patel`, `STU-003 Rohan Verma`).
19. `assessments`: Assessment test session envelopes.
20. `assessment_questions`: Question sequence per assessment.
21. `student_answers`: Evaluated student responses with marks, times, and timestamps.
22. `learner_concept_mastery`: Concept-level mastery scores, Bayesian confidence ratings, and attempt history.
23. `student_misconceptions`: Evidence-based misconception log (`SUSPECTED`, `CONFIRMED`, `RESOLVED`) with `evidence_text`.

### E. P4 Remediation, Spaced Repetition & Vector RAG (3 Tables)
24. `spaced_repetition_schedules`: Leitner/SM-2 revision intervals, ease factors, and due dates.
25. `remediation_records`: Diagnostic remediation logs, prerequisite links, and practice attempts.
26. `curriculum_embeddings`: Chunked NCERT textbook content with `vector(2048)` embeddings.

---

## 4. Supabase Storage: Private PDF Source Bucket

A private storage bucket was provisioned and verified:
- **Bucket ID**: `curriculum-sources`
- **Public Access**: `False` (Enforces authenticated access)
- **Allowed MIME Types**: `['application/pdf']`
- **File Size Limit**: 50 MB
- **Uploaded Artifacts**: NCERT Class 10 Science Chapter 1 textbook (`jesc101.pdf`).

---

## 5. AI Embedding Model Migration & Live RAG Indexing

During initial P4 vector indexing against the NVIDIA Integrate endpoint, the previously referenced model `nvidia/nv-embedqa-e5-v5` returned an `HTTP 410 Gone` error, as NVIDIA deprecated this model on August 25, 2026.

### 5.1 Model Selection & Verification
To resolve this deprecation, live model querying of the NVIDIA Integrate API (`https://integrate.api.nvidia.com/v1/models`) was performed. The state-of-the-art replacement model was selected:
- **Active Model**: `nvidia/nemotron-3-embed-1b`
- **Dimensionality**: $2048$ floating-point dimensions
- **API Status**: Active & Live (`HTTP 200 OK`)
- **Query Type**: Asymmetric embeddings supporting `input_type="passage"` and `input_type="query"`.

### 5.2 NCERT Chunking & Indexing Pipeline (`scripts/index_ncert_rag.py`)
1. **Source Document**: Extracted text from `sources/jesc101.pdf` (16 pages of NCERT Class 10 Science Chapter 1).
2. **Text Chunking**: Segmented into 16 pedagogically coherent sections aligning with NCERT headings (Chemical Equations, Balancing Equations, Combination Reactions, Decomposition Reactions, Displacement Reactions, Double Displacement & Precipitation, Oxidation & Reduction, Corrosion & Rancidity).
3. **Embedding Generation**: Processed through `nvidia/nemotron-3-embed-1b` with `input_type="passage"`.
4. **Cloud & Local Storage**: Synchronously stored in SQLite `curriculum_embeddings` and Supabase PostgreSQL `curriculum_embeddings` as `vector(2048)`.
5. **Retrieval Verification**:
   - Query: `"barium sulphate precipitate double displacement"`
   - pgvector Operator: `<=>` (Cosine distance)
   - Result: Correctly retrieved Chunk `CHK-CH01-P011` (Page 11, Section 1.2.4) with similarity $> 0.82$.

---

## 6. Zero API Key Leakage Audit

To adhere to strict security protocols, the developer's credentials (NVIDIA API key, Bodhan API key, Supabase database password, Supabase anon/publishable keys) are maintained exclusively in the private `.env` file.

The automated secret audit script (`scripts/audit_api_leaks.py`) scans all source files, documentation, test files, and reports:

```
[AUDIT] Scanning workspace against 4 registered secret signatures...
[AUDIT PASSED] Verification Confirmed:
 -> Zero API keys or secrets found in codebase outside .env
```

---

## 7. Dual-Engine RAG Service Architecture

The BodhAI RAG service (`src/services/rag_service.py`) incorporates automated failover:

```
+-------------------------------------------------------------------------+
|                         Student Query / Topic                           |
+-------------------------------------------------------------------------+
                                     |
                                     v
                  +--------------------------------------+
                  | Generate Query Embedding (NVIDIA API)|
                  +--------------------------------------+
                         /                      \
               (Success & DB Live)          (Offline / API Failure)
                       /                          \
                      v                            v
       +----------------------------+     +-------------------------------+
       | Supabase PostgreSQL Vector |     | Local SQLite Lexical Matcher  |
       | Cosine Distance: <=>       |     | TF-IDF / Token Overlap Search |
       +----------------------------+     +-------------------------------+
                      \                            /
                       \                          /
                        v                        v
            +-----------------------------------------------+
            | Grounded NCERT Context, Page #, & Explanation |
            +-----------------------------------------------+
```

This guarantees high availability: whether the student is connected to cloud infrastructure or operating locally, textbook grounding is always returned.
