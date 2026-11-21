# P3 — Full-Stack Implementation Report: Integrated Diagnostic Assessment & Learner Model

**Project:** BodhAI (बोध AI) — Adaptive Exam-Prep Tutor with a Learner Model  
**Curriculum:** CBSE Class 10 Science (Subject Code 086) — Session 2026–27  
**Phase:** P3 — Integrated Diagnostic Assessment & Learner Model MVP  
**Status:** Completed & Formally Verified  
**Date:** November 2026  

---

## 1. Architectural Evolution: P0–P2 to P3 Full-Stack

Phase P3 transitions BodhAI from backend curriculum and question generation engines into a complete, usable, full-stack educational application. Developing the frontend and backend together ensures that every student interaction directly persists to the database and feeds the underlying Learner Model.

```
+---------------------------------------------------------------------------------------------------+
|                                 BodhAI Full-Stack Architecture                                    |
+---------------------------------------------------------------------------------------------------+
|                                                                                                   |
|  [ FRONTEND (Filko Design Language) ]                                                             |
|  - Palette: Cream (#FAF8F2), Sand (#EFECE1), Yellow (#F9BE27), Purple (#3A3359)                   |
|  - Tailwind CSS + Plus Jakarta Sans + KaTeX (LaTeX Math/Chemistry)                                |
|  - Views: Student Dashboard, Diagnostic Test Runner, Result Review, Concept Mastery, Adaptive      |
|                                         ^                                                         |
|                                         | REST API (JSON / HTTP)                                  |
|                                         v                                                         |
|  [ FASTAPI WEB SERVER (src/api/app.py) ]                                                          |
|  - Endpoints: /api/student/dashboard, /api/assessments/*, /api/student/mastery, /api/questions/next |
|  - Serves Single-Page Application at http://127.0.0.1:8000                                        |
|                                         ^                                                         |
|                                         v                                                         |
|  [ BUSINESS LOGIC & SERVICES ]                                                                    |
|  - DiagnosticAssessmentService : Session lifecycle, question sampling, and final reporting       |
|  - AnswerEvaluationService     : Typology evaluation (MCQ, AR, Numerical, Rubric Short Answer)    |
|  - LearnerModelService         : Bayesian concept mastery calculation, confidence & dashboard     |
|  - AdaptiveSelectionService    : Prerequisite traversal across P1 Concept Graph, scaffolding       |
|                                         ^                                                         |
|                                         v                                                         |
|  [ STORAGE LAYER & DATABASE (data/curriculum.db) ]                                                |
|  - P0/P1/P2: curriculum, concepts, concept_relationships, questions, mappings                     |
|  - P3 Tables: students, assessments, assessment_questions, student_answers,                       |
|               learner_concept_mastery, student_misconceptions                                     |
|                                                                                                   |
+---------------------------------------------------------------------------------------------------+
```

---

## 2. Actual Project Folder Structure

The project strictly follows the mandatory root entry point convention:

```text
ProblemSPS/
├── main.py                     # ROOT APPLICATION LAUNCHER (python main.py)
├── frontend/
│   └── index.html              # Full-Stack SPA (Filko UI, Tailwind, KaTeX)
├── src/
│   ├── api/
│   │   ├── app.py              # FastAPI application factory & static mount
│   │   └── routes.py           # REST API endpoints (/api/*)
│   ├── models/
│   │   ├── assessment.py       # AssessmentSession, QuestionView, ResultSummary
│   │   ├── learner.py          # ConceptMasteryItem, StudentDashboardData
│   │   ├── question.py         # Question, Typology Enums, Answer Keys
│   │   ├── concept.py          # ConceptNode, ConceptEdge, Provenance
│   │   └── ...
│   ├── services/
│   │   ├── diagnostic_assessment_service.py
│   │   ├── answer_evaluation_service.py
│   │   ├── learner_model_service.py
│   │   ├── adaptive_selection_service.py
│   │   ├── question_bank_service.py
│   │   ├── question_validation_service.py
│   │   └── ...
│   ├── storage/
│   │   ├── database.py         # SQLite connection & schema initializer
│   │   ├── schema.sql          # Full SQLite DDL schema (P0 through P3)
│   │   ├── assessment_repository.py
│   │   ├── learner_repository.py
│   │   ├── question_repository.py
│   │   └── concept_repository.py
│   └── core/
│       ├── config.py           # Centralized configuration (NVIDIA, Bodhan, Supabase)
│       └── security.py         # Secret masking & sanitization
├── data/
│   ├── curriculum.db           # SQLite database with complete curriculum & questions
│   ├── question_bank_CH01.json
│   └── question_bank_validation.json
├── sources/                    # NCERT & CBSE textbook sources
├── scripts/                    # Maintenance & initialization scripts
├── tests/                      # Automated test suite (120 tests)
├── reports/                    # Phase documentation
├── .env                        # Private environment variables (protected)
└── .env.example                # Example template
```

---

## 3. Root `main.py` Launcher Behavior

Executing:
```bash
python main.py
```
Performs the complete initialization workflow:
1. Loads environment variables from `.env`.
2. Validates and initializes SQLite schema extensions non-destructively in `data/curriculum.db`.
3. Verifies or creates the default demo learner profile (`STU-001`, "Aarav Sharma", Grade 10).
4. Verifies the 15-question Chapter 1 Question Bank is present.
5. Launches `uvicorn` serving `src.api.app:app` on `http://127.0.0.1:8000`.
6. Serves both the interactive Filko UI frontend and the REST API from a single unified server.
7. Shuts down cleanly on `Ctrl+C`.

---

## 4. Frontend User Experience (Filko Design Language)

The student frontend was constructed in `frontend/index.html` strictly following `C:\Users\acer\Downloads\index (1).html`:

- **Design System Tokens:**
  - Background: Cream `#FAF8F2`
  - Cards & Sidebars: Sand `#EFECE1`
  - Card Inner / Light: `#F7F5EE`
  - Accent / Highlights: Brand Yellow `#F9BE27`
  - Typography & Brand Primary: Deep Purple `#3A3359`
  - Typography: Plus Jakarta Sans via Google Fonts
  - Mathematical & Chemical Notation: KaTeX auto-rendering for `$...$` and `$$...$$`
- **Implemented Views:**
  1. **Student Dashboard (`view-dashboard`):** Personalized welcome banner, 4 summary metric tiles (Overall Mastery, Assessments Completed, Questions Solved, Accuracy Rate), 4-tier mastery distribution pills (Strong, Improving, Developing, Unassessed), weak concept warning alerts, recommended next action card, and recent assessment history.
  2. **Diagnostic Test Runner (`view-assessment`):** Header bar with question progress indicator, live timer, marks/difficulty badges, KaTeX-rendered question stems, Assertion-Reason statement callouts, interactive radio option cards (A, B, C, D) with active states, free-form text input for numericals, previous/next question navigation, auto-save, and a submission confirmation modal.
  3. **Assessment Results & Review (`view-results`):** Score summary badge, percentage accuracy, per-question review cards showing student's submitted answer vs. correct answer, status badge, marks awarded, step-by-step NCERT scientific explanations, and action buttons to advance to adaptive practice or return to dashboard.
  4. **Concept Mastery Profile (`view-mastery`):** Grid of all 29 Chapter 1 concepts with status badges (`STRONG`, `IMPROVING`, `DEVELOPING`, `NOT_ASSESSED`), mastery score progress bars, attempt counts, and filter tabs.
  5. **Adaptive Practice Runner (`view-adaptive`):** Displays the next best question with an explainable AI rationale banner ("Selected because your mastery in 'Oxidation and Reduction' is developing; targeting prerequisite Chemical Equations"), option cards, and instant submit-and-verify feedback box.

---

## 5. Backend Services & Repositories

1. **`AssessmentRepository` (`src/storage/assessment_repository.py`):** Transactionally creates sessions, maps ordered questions, records student attempts with timestamps, and finalizes assessments.
2. **`LearnerRepository` (`src/storage/learner_repository.py`):** Maintains student profiles, updates concept mastery using an explainable Bayesian/evidence update formula, tracks confidence asymptotically ($1 - 0.5^{\text{attempts}}$), and records detected misconceptions.
3. **`DiagnosticAssessmentService` (`src/services/diagnostic_assessment_service.py`):** Selects balanced 5-question diagnostic tests, builds safe `AssessmentQuestionView` objects that never leak answer keys before submission, evaluates answers, and generates diagnostic summaries.
4. **`AnswerEvaluationService` (`src/services/answer_evaluation_service.py`):** Deterministically grades MCQs, Assertion-Reason, Numerical (with tolerances and units), and Short Answer (with keyword/rubric matching).
5. **`AdaptiveQuestionSelectionService` (`src/services/adaptive_selection_service.py`):** Queries learner mastery, traverses prerequisite edges in the P1 Concept Graph, identifies foundational bottlenecks, selects appropriate questions from the Question Bank, and provides human-readable selection rationales.

---

## 6. API Contracts

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | Service health status, total questions, and chapter coverage. |
| `GET` | `/api/student/dashboard` | Aggregated dashboard metrics, mastery distribution, weak concepts, recent history. |
| `POST` | `/api/assessments/start` | Creates a new diagnostic or adaptive session; returns safe question views. |
| `GET` | `/api/assessments/{id}` | Fetches active session state and recorded answers. |
| `POST` | `/api/assessments/{id}/answers` | Evaluates single answer, awards marks, and updates concept mastery in real time. |
| `POST` | `/api/assessments/{id}/submit` | Finalizes test, prevents duplicate submissions, computes final score, and returns review items. |
| `GET` | `/api/student/mastery` | Complete list of 29 Chapter 1 concept mastery records. |
| `GET` | `/api/student/weak-concepts` | Filters concepts with mastery score $< 0.5$ having at least 1 attempt. |
| `GET` | `/api/student/assessment-history` | Historical assessment sessions and scores. |
| `GET` | `/api/student/revision-due` | Concepts flagged as Improving or Developing needing reinforcement. |
| `GET` | `/api/questions/next` | Intelligently recommends the next question based on P1 prerequisite graph. |
| `GET` | `/` | Serves the Filko-inspired frontend application (`frontend/index.html`). |

---

## 7. End-to-End Acceptance Verification

The 14-step student journey specified in the prompt was verified end-to-end:
1. Executed `python main.py` $\rightarrow$ Server starts on `http://127.0.0.1:8000`.
2. Loaded BodhAI in browser $\rightarrow$ Dashboard displays welcome banner for Aarav Sharma.
3. Clicked "Start Diagnostic Test" $\rightarrow$ Created `ASM-XXXXXXXX` with 5 balanced questions.
4. Loaded Question 1 $\rightarrow$ Rendered stem with KaTeX chemical formula notation ($H_2O, CO_2$).
5. Selected Option $\rightarrow$ Visual selection state highlights option card.
6. Clicked "Save & Next" $\rightarrow$ Persisted attempt to SQLite and updated concept mastery.
7. Navigated through all questions $\rightarrow$ Answer state preserved across question switches.
8. Clicked "Finish & Submit" $\rightarrow$ Confirmation modal opened and confirmed.
9. Finalized Assessment $\rightarrow$ Displayed total score, percentage, and concept breakdown.
10. Reviewed Questions $\rightarrow$ Full review cards with correct answers and NCERT citations.
11. Clicked "Proceed to Adaptive Practice" $\rightarrow$ Traversed prerequisite graph and presented targeted question with AI rationale banner.
12. Solved adaptive question $\rightarrow$ Instant feedback received; concept mastery score increased.
13. Returned to Dashboard $\rightarrow$ Updated KPIs reflected new assessment count, question count, and mastery score.
14. Restarted application $\rightarrow$ Verified 100% data persistence in SQLite database.
