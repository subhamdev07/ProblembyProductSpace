# P2 — Question Bank & Question Generation Engine Specification

**Project:** Adaptive Exam-Prep Tutor with a Learner Model  
**Curriculum:** CBSE Class 10 Science (Subject Code 086)  
**Academic Session:** 2026–27  
**Phase:** P2 — Question Bank & Question Generation Engine  
**Status:** Completed & Formally Verified  
**Date:** November 2026  

---

## 1. Executive Summary

Phase P2 delivers the assessment foundation for the Adaptive Exam-Prep Tutor: a high-integrity Question Bank and an AI-assisted Question Generation Engine. This engine grounds assessment items directly in the P0 Curriculum Hierarchy (Syllabus Foundation) and P1 Concept Graph, enforcing strict adherence to official CBSE Class 10 Science guidelines for the 2026–27 academic session.

The architecture ensures that every question is:
1. **Curriculum-Grounded:** Mapped to official CBSE units, chapters, topics, and learning outcomes.
2. **Concept-Anchored:** Linked directly to validated nodes in the P1 Concept Graph for adaptive learner diagnostics and misconception tracking.
3. **Pedagogically Rigorous:** Classified by cognitive levels (CBSE Bloom's blueprint) and difficulty bands.
4. **Source-Attributed:** Supported by verbatim provenance from the NCERT Class 10 Science textbook.
5. **Deterministically Validated:** Verified against a 12-point quality validation engine.

---

## 2. Question Typology Architecture

The system supports seven distinct question typologies corresponding to the official CBSE examination pattern for Class 10 Science:

| Question Typology | Identifier | Typical Marks | Typical Duration | Structure & Answer Key Requirements |
| :--- | :--- | :---: | :---: | :--- |
| **Multiple Choice (MCQ)** | `MCQ` | 1 | 45–60 s | Exactly 4 options (`A`, `B`, `C`, `D`), unambiguous single correct option key, distractor rationales. |
| **Assertion & Reason** | `ASSERTION_REASON` | 1 | 60–90 s | Two statements (Assertion and Reason), standard 4-choice response (`A`: both true and R explains A; `B`: both true but R does not explain A; `C`: A true R false; `D`: A false R true). |
| **Short Answer** | `SHORT_ANSWER` | 2–3 | 90–180 s | 2 to 3 marks requiring clear point-by-point marking rubric (`key_points`), balanced chemical equations, and sample answers. |
| **Long Answer** | `LONG_ANSWER` | 5 | 300–450 s | Multi-part structured question with comprehensive marking scheme, subdivided into sub-parts (e.g., (a), (b), (c)) with allocated marks per step. |
| **Case-Based / Source-Based** | `CASE_BASED` | 4 | 300–420 s | Stem consists of a factual experimental or real-world passage followed by 2 to 4 structured sub-questions with internal choices per CBSE guidelines. |
| **Numerical / Quantitative** | `NUMERICAL` | 2–3 | 120–240 s | Quantitative stoichiometric or physics problem requiring numeric answer, physical units, acceptable tolerance interval, and step-by-step calculation steps. |
| **Diagram-Based / Visual** | `DIAGRAM_BASED` | 2–4 | 120–240 s | Experimental apparatus setup, ray diagram, or reaction apparatus with specific labeling prompts and observation questions. |

---

## 3. Cognitive Taxonomy & CBSE Blueprint Alignment

The question bank strictly complies with the **CBSE Assessment Taxonomy Blueprint** specified in the official CBSE Science Curriculum 2026–27 (Page 9):

```
       CBSE Question Paper Blueprint (80 Marks Theory)
+--------------------------------------------------------------+
| Demonstrate Knowledge & Understanding (Recall, Facts)  : 50% |
| Application of Knowledge & Concepts (Solve, Apply)    : 30% |
| Formulate, Analyze, Evaluate & Create (High Order)     : 20% |
+--------------------------------------------------------------+
```

### 3.1 Cognitive Levels

1. **`KNOWLEDGE_UNDERSTANDING` (50% target):**
   - Focus: State laws, define terms, identify components, recall formulas, state observations.
   - Example: Identifying physical observations that determine a chemical reaction, defining precipitation reactions.
2. **`APPLICATION` (30% target):**
   - Focus: Apply concepts to novel situations, balance chemical equations, calculate stoichiometric masses, predict displacement reactions.
   - Example: Predicting whether iron displaces copper from copper sulfate solution, writing balanced state equations.
3. **`ANALYZE_EVALUATE_CREATE` (20% target):**
   - Focus: Multi-step inference, experimental error evaluation, synthesis of redox mechanisms, interpreting industrial and biological processes.
   - Example: Analyzing why respiration is an exothermic reaction, decomposing white silver chloride in sunlight, stoichiometric conservation proofs.

### 3.2 Difficulty Calibration Rubric

| Difficulty | Criteria | Target Student Persona |
| :--- | :--- | :--- |
| **`EASY`** | Single-step direct recall or recognition; straightforward terminology; definitions verbatim from NCERT; minimum distractors. | Foundations / Beginner learners establishing concept mastery. |
| **`MEDIUM`** | Two-step conceptual reasoning; balancing non-trivial chemical equations; selecting correct observations with plausible distractors. | Grade-level proficiency; standard CBSE board examination expectation. |
| **`HARD`** | Multi-concept synthesis; quantitative stoichiometric calculations; case-based experimental scenarios; identifying subtle oxidation-reduction pairs. | Advanced exam-prep; diagnostic identification of misconception gaps. |

---

## 4. Concept Graph Referential Integrity

Questions in P2 are not isolated items; each question functions as a diagnostic probe into the **P1 Concept Graph**:

- **Primary & Secondary Concept Association:** Every question is mapped to one or more concept nodes via the `question_concept_mappings` relational table.
- **Prerequisite Diagnostic Routing:** When a student answers incorrectly, the learner model traces the prerequisite edges in the concept graph (e.g., failure on `CPT-CH01-003` "Balanced Chemical Equation" triggers diagnostics on `CPT-CH01-002` "Law of Conservation of Mass").
- **Misconception Tagging:** Every question specifies explicit misconception tags (e.g., `confusing_rusting_with_corrosion_of_all_metals`, `assuming_mass_decreases_in_open_gas_reactions`), enabling targeted remediation.

---

## 5. CBSE Learning Outcome Alignment & Formative Exclusion

Each question links to official CBSE Learning Outcomes via `question_learning_outcome_mappings`:

- **Formative vs. Summative Boundary:** The engine enforces that topics or activities categorized in the CBSE Syllabus as formative-only (such as practical observations or portfolio tasks) are not weighted as summative board exam items.
- **Curriculum Breadth:** Questions ensure balanced coverage across all textbook sections (chemical equations, reaction types, oxidation-reduction, corrosion, and rancidity).

---

## 6. Design System & Visual Compatibility (Filko UI Alignment)

While P2 focuses strictly on backend engine and assessment data structures, all question models and text formatting are engineered for seamless presentation within the **Filko UI Design Language** (`index (1).html`):

- **Palette Specifications:**
  - Background: Cream `#FAF8F2`
  - Container / Card: Sand `#EFECE1`
  - Accent / Highlights: Yellow `#F9BE27`
  - Primary / Typography: Deep Purple `#3A3359`
- **Mathematical & Chemical Notation:** Question stems, options, and explanations use standard LaTeX syntax enclosed in `$...$` (e.g., `$2\mathrm{Mg} + \mathrm{O}_2 \rightarrow 2\mathrm{MgO}$`), rendering cleanly via KaTeX or MathJax.
- **Structured Option Containers:** MCQ and Assertion-Reason options are formatted as discrete dictionary entries (`A`, `B`, `C`, `D`) for direct binding to interactive UI radio buttons or tiles.

---

## 7. Artifacts Summary

| Artifact | Location | Description |
| :--- | :--- | :--- |
| Domain Models | `src/models/question.py` | Pydantic v2 domain models and answer key validators. |
| SQLite Schema | `src/storage/schema.sql` | `questions`, `question_concept_mappings`, `question_learning_outcome_mappings`. |
| Storage Layer | `src/storage/question_repository.py` | Transactional persistence, CRUD, multi-dimensional queries. |
| Validation Engine | `src/services/question_validation_service.py` | 12-rule deterministic validation service. |
| Generation Engine | `src/services/question_generation_service.py` | AI generation grounded in concepts with hermetic mock capability. |
| Chapter 1 Bank | `src/services/question_bank_service.py` | Curated 15-question benchmark bank. |
| JSON Exports | `data/question_bank_CH01.json` | Complete export of 15 validated questions. |
| Validation JSON | `data/question_bank_validation.json` | 100% pass audit summary. |
