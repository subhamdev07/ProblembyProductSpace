# P3 — Execution & Handover Report

**Project:** BodhAI (बोध AI) — Adaptive Exam-Prep Tutor with a Learner Model  
**Curriculum:** CBSE Class 10 Science (Subject Code 086) — Session 2026–27  
**Phase:** P3 — Integrated Diagnostic Assessment & Learner Model MVP  
**Status:** Completed & Formally Handed Over  
**Date:** November 2026  

---

## 1. Quick Start Guide

### 1.1 Prerequisites
- **Python:** 3.10 or higher (Verified on Python 3.14.6)
- **Web Browser:** Any modern evergreen browser (Chrome, Edge, Firefox, Safari)
- **Dependencies:** All required packages are pre-installed in the workspace virtual environment (`fastapi`, `uvicorn`, `pydantic`, `requests`, `python-dotenv`, `fitz`, `openai`).

### 1.2 Running the Application
From the workspace root directory, execute:

```bash
python main.py
```

### 1.3 Expected Console Output
```text
======================================================================
  BodhAI (बोध AI) — Adaptive Exam-Prep Tutor
  CBSE Class 10 Science | Academic Session 2026–27
======================================================================
  [DB] SQLite Database Verified: data/curriculum.db
  [STUDENT] Active Demo Learner: Aarav Sharma (STU-001)
  [ASSESSMENT] Question Bank: 15 verified questions
  [DIAGNOSTICS] Concept Graph: 29 concepts tracked across Chapter 1
----------------------------------------------------------------------
  🚀 BodhAI Full-Stack App URL: http://127.0.0.1:8000
  📖 Interactive API Docs:     http://127.0.0.1:8000/docs
  🩺 Health Check Endpoint:     http://127.0.0.1:8000/api/health
======================================================================
  Press Ctrl+C to stop the server.

INFO:     Started server process [XXXX]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

### 1.4 Opening BodhAI
Open your browser and navigate to:
$$\text{\texttt{http://127.0.0.1:8000}}$$

You will be greeted by the Filko-inspired Student Dashboard displaying:
- Welcome banner for student **Aarav Sharma**.
- Real-time KPI summary (Overall Mastery, Assessments Completed, Accuracy).
- Primary CTA button to **Start Diagnostic Test**.
- Concept Mastery Status overview.

---

## 2. Environment Configuration

The application reads configuration from `.env` (with a clean template in `.env.example`):

| Variable | Description | Status |
| :--- | :--- | :---: |
| `SUPABASE_URL` | Supabase Project Gateway URL (`https://fewqvskzdnkokeibanet.supabase.co`) | Configured |
| `SUPABASE_ANON_KEY` | Supabase Publishable / Anon Client Key (`sb_publishable_...`) | Configured |
| `SUPABASE_DB_PASSWORD` | Supabase PostgreSQL Database Password (`Subham***`) | Configured |
| `SUPABASE_DB_URL` | Direct PostgreSQL connection URI (`postgresql://postgres:...`) | Configured & Synced (23 Tables) |
| `SUPABASE_SERVICE_ROLE_KEY` | Administrative secret key for remote storage & DDL migrations | Optional / Cloud |
| `NVIDIA_API_KEY` | NVIDIA integrate API Key for Nemotron 30B LLM | Configured |
| `BODHAN_API_KEY` | Bodhan API Key for Indic-OCR document extraction | Configured |
| `EMBEDDING_MODEL` | Text embedding model identifier (`nvidia/nv-embedqa-e5-v5`) | Configured |

*Note: BodhAI features full offline-first standalone capabilities. If external cloud services or network connectivity are unavailable, the local SQLite database (`data/curriculum.db`), question bank, and deterministic evaluation engine ensure uninterrupted functionality.*

---

## 3. Running Automated Tests

To execute the complete 120-test multi-phase regression suite (P0 through P3):

```bash
python -m pytest tests -v
```

To run only the P3 assessment, learner model, and API test suites:

```bash
python -m pytest tests/test_p3_assessment_and_learner.py tests/test_p3_api.py -v
```

To verify zero API credential leaks across the codebase:

```bash
python scripts/audit_api_leaks.py
```

---

## 4. Current Implementation Status Summary

| Capability | Module / Layer | Status |
| :--- | :--- | :---: |
| **Root Application Entry Point** | `main.py` | **Complete & Verified** |
| **Filko-Inspired Single-Page UI** | `frontend/index.html` | **Complete & Verified** |
| **Student Dashboard & KPIs** | `GET /api/student/dashboard` | **Complete & Verified** |
| **Diagnostic Assessment Runner** | `POST /api/assessments/start` | **Complete & Verified** |
| **Real-Time Answer Evaluation** | `POST /api/assessments/{id}/answers` | **Complete & Verified** |
| **Assessment Finalization & Review** | `POST /api/assessments/{id}/submit` | **Complete & Verified** |
| **Bayesian Learner Concept Mastery** | `src/services/learner_model_service.py` | **Complete & Verified** |
| **P1 Prerequisite Graph Traversal** | `src/services/adaptive_selection_service.py` | **Complete & Verified** |
| **Misconception Evidence Logging** | `src/storage/learner_repository.py` | **Complete & Verified** |
| **Relational SQLite Persistence** | `data/curriculum.db` | **Complete & Verified** |

---

## 5. Roadmap Ahead: Next Phases

1. **Phase P4 (Formative Practice & Targeted Remediation):**
   - Micro-lesson modules linking specific NCERT sections and textbook activities.
   - Socratic dialogic tutoring with NVIDIA Nemotron when a student misses 2 consecutive items in a concept.
   - Flashcard drills for chemical formulae and reaction balancing.
2. **Phase P5 (CBSE Exam Simulation & Mock Blueprint):**
   - Full 80-mark, 39-question CBSE Board Exam simulation with section breakdown (Sections A, B, C, D, E).
   - Strict 3-hour exam timer with section-wise time warnings.
   - Formal letter-grade projection based on historical CBSE Class 10 cutoffs.
