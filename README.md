# Adaptive Exam-Prep Tutor with a Learner Model
### Curriculum: CBSE Class 10 Science (Subject Code 086) — Session 2026–27

---

## 1. Overview & Current Project Status

- **Phase P0 (Syllabus Foundation):** ✅ **COMPLETE & VERIFIED**
  - 5 CBSE Units (`UNIT-01` to `UNIT-05`) with 80 theory marks preserved.
  - 13 official NCERT Chapters (`CH-01` to `CH-13`).
  - 48 Topics and 105 Subtopics with explicit assessment classifications (`SUMMATIVE`, `FORMATIVE`, `NOT_IN_CURRENT_SCOPE`).
  - 15 official Curricular Goals and Competencies (`CG 1–CG 8`, `C 1.1–C 8.2`).
  - Relational SQLite database with foreign key constraints (`data/curriculum.db`).
  - 12-rule Curriculum Validation Engine (100% clean pass, 0 errors).
- **Phase P0.5 (AI Infrastructure Integration):** ✅ **COMPLETE & VERIFIED**
  - **NVIDIA Nemotron 3.5 Lightning 30B A3B:** Centralized OpenAI-compatible service (`src/ai/llm_service.py`), supporting thinking tokens, streaming, non-streaming, JSON mode, and retry backoffs.
  - **Bodhan Indic-OCR:** Document OCR service (`src/ai/ocr_service.py`) with Base64 encoding, vision chat completion payloads, and error normalization.
  - **Hybrid Document Ingestion Pipeline:** `DocumentProcessor` (`src/ai/document_processor.py`) routes text-rich pages to PyMuPDF native extraction and scanned/diagram pages to Bodhan OCR.
  - **Security & Privacy:** Reasoning tokens are kept internal; student responses never leak internal reasoning; API keys are masked in logs and configuration summaries.
  - **Test Suite:** **52 / 52 automated tests passing** (zero API tokens consumed via isolated mocks).

---

## 2. Directory Layout

```
ProblemSPS/
├── sources/                               # Primary authority documents
│   ├── Science_SecP1_2026-27.pdf          # Official CBSE Class 10 Science Syllabus 2026-27
│   └── jesc101.pdf                        # NCERT Class 10 Science Chapter 1 Textbook
├── src/
│   ├── core/                              # Core configuration, security & exceptions
│   │   ├── config.py                      # NVIDIA & Bodhan environment settings
│   │   ├── security.py                    # Secret masking & log sanitization
│   │   └── exceptions.py                  # AI infrastructure typed exceptions
│   ├── ai/                                # AI Services & Document Ingestion
│   │   ├── models.py                      # LLMMessage, LLMResponse, OCRPageResult, etc.
│   │   ├── llm_service.py                 # Centralized NVIDIA Nemotron LLM service
│   │   ├── ocr_service.py                 # Dedicated Bodhan Indic-OCR service
│   │   └── document_processor.py          # Hybrid PyMuPDF + Bodhan OCR ingestion pipeline
│   ├── models/                            # Pydantic v2 curriculum models
│   ├── storage/                           # SQLite repository & schema.sql
│   └── services/                          # Curriculum hierarchy & validation services
├── data/                                  # Exported database & machine-readable JSON
│   ├── curriculum.db                      # Relational SQLite database
│   ├── curriculum_data.json               # Canonical hierarchical JSON export
│   ├── source_documents.json              # Source documents audit export
│   └── validation_results.json            # 12-rule curriculum validation results
├── tests/                                 # 52 automated Pytest test cases
├── reports/                               # Complete audit, foundation & architecture reports
│   ├── P0-Syllabus-Foundation.md
│   ├── P0-Implementation-Report.md
│   ├── P0-Source-Audit.md
│   ├── P0-Validation-Report.md
│   ├── P0.5-LLM-Integration-Report.md
│   ├── P0.5-OCR-Integration-Report.md
│   ├── P0.5-Architecture-Report.md
│   └── P0.5-Validation-Report.md
├── scripts/
│   └── smoke_test_ai.py                   # Optional smoke test for live AI credentials
├── main.py                                # P0 pipeline runner
├── .env.example                           # Template environment configuration
└── README.md
```

---

## 3. Running Tests and Verification

### Run the full test suite (52 tests across P0 and P0.5):
```bash
python -m pytest tests -v
```

### Run P0 Master Curriculum Pipeline:
```bash
python main.py
```

### Run AI Infrastructure Configuration Check / Dry Run:
```bash
python scripts/smoke_test_ai.py
```

---

## 4. Strict Scope Governance

- **Zero Git commands or operations were performed.**
- Future phases (**P1: Concept Graph**, **P2: Diagnostic Assessment**, **P3: Learner Model**, etc.) have not been started and await explicit approval.
