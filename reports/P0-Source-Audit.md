# P0 — Source Audit Report

**Academic Session:** 2026–27  
**Subject:** CBSE Class 10 Science (Subject Code 086)  
**Authority:** Central Board of Secondary Education (CBSE) / NCERT  

---

## 1. Executive Summary

This audit verifies the primary source documents utilized to construct the P0 Syllabus Foundation.
In strict adherence to project requirements, **no source evidence was fabricated**.
The primary curriculum authority is the official CBSE Class 10 Science Curriculum PDF for 2026–27.
Where NCERT textbook material is present in the workspace (`sources/jesc101.pdf`), chapter content has been verified to page-level precision.
Where NCERT textbook chapters are absent (Chapters 2 through 13), chapter titles and curriculum-level topics are anchored directly in the official CBSE syllabus, and textbook-level section pagination is transparently documented as pending external source acquisition.

---

## 2. Available Primary Source Documents

| Document ID | Official Title | Document Type | Authority | File Path | Pages | SHA-256 Digest | Status |
|---|---|---|---|---|:---:|---|:---:|
| `CBSE_SCI_10_2026_27` | CBSE Secondary School Curriculum 2026-27: Science (Class X, Subject Code 086) | `OFFICIAL_SYLLABUS` | Central Board of Secondary Education (CBSE) | `sources/Science_SecP1_2026-27.pdf` | 9 | `7f1f8bd170b7...` | **VERIFIED** |
| `NCERT_SCI_10_CH01` | NCERT Class X Science Textbook - Chapter 1: Chemical Reactions and Equations | `TEXTBOOK_CHAPTER` | National Council of Educational Research and Training (NCERT) | `sources/jesc101.pdf` | 16 | `9d58fa614b2d...` | **VERIFIED** |

---

## 3. Page-Wise Content Extraction Map

### Primary Source: `CBSE_SCI_10_2026_27` (`Science_SecP1_2026-27.pdf`)

| Page(s) | Section Heading | Extracted Content & Pedagogical Entities | Verification Verdict |
|:---:|---|---|:---:|
| **1** | Introduction & Vision | NEP 2020 & NCF-SE 2023 principles, multidisciplinary inquiry approach | VERIFIED |
| **2–4** | Curricular Goals (CGs) & Competencies (Cs) | CG 1 through CG 8, Competencies C 1.1 through C 8.2, suggestive verbs | VERIFIED |
| **4** | Course Structure (Annual Exam) | 5 CBSE Units with mark allocations (Total Theory: 80 marks; IA: 20 marks) | VERIFIED |
| **4** | Unit I: Chemical Substances | Chemical Reactions and Equations topics, Types of reactions, Redox | VERIFIED |
| **4** | Note on Formative Topics | Periodic Classification of Elements (Döbereiner to Modern Table) — FORMATIVE ONLY | VERIFIED |
| **4–5** | Unit I: Acids, Bases and Salts | H+/OH- definitions, indicators, pH scale (log def excluded), salt preparations | VERIFIED |
| **5** | Unit I: Metals and Non-Metals | Properties, reactivity series, ionic compounds, metallurgy, corrosion | VERIFIED |
| **5** | Unit I: Carbon and its Compounds | Covalent bonding, homologous series, nomenclature, reactions, soaps | VERIFIED |
| **5** | Unit II: World of Living | Life processes: nutrition, respiration, transport, excretion | VERIFIED |
| **5** | Unit II: Control and Coordination | Tropic movements, plant hormones, nervous system, reflex action, animal hormones | VERIFIED |
| **5** | Unit II: Reproduction | Asexual & sexual reproduction in plants and humans, reproductive health, family planning | VERIFIED |
| **5** | Unit II: Heredity | Mendel’s laws, monohybrid/dihybrid cross, sex determination | VERIFIED |
| **5–6** | Note on Formative Topics | Evolution (traits, speciation, fossils, human evolution) — FORMATIVE ONLY | VERIFIED |
| **5–6** | Unit III: Natural Phenomena | Reflection, spherical mirrors, refraction, lenses, lens formula, power | VERIFIED |
| **6** | Unit III: Human Eye | Eye lens functioning, vision defects, dispersion, scattering (sun colour excluded) | VERIFIED |
| **6** | Unit IV: Effects of Current | Ohm’s law, resistance, series/parallel combinations, Joule’s heating, power | VERIFIED |
| **6** | Unit IV: Magnetic Effects | Magnetic fields, conductors, solenoids, Fleming's Left-Hand Rule, AC/DC, domestic circuits | VERIFIED |
| **6** | Note on Formative Topics | Electric Motor, Electromagnetic Induction, Electric Generator — FORMATIVE ONLY | VERIFIED |
| **6** | Unit V: Natural Resources | Ecosystem, ozone depletion, waste solutions, biodegradable/non-biodegradable | VERIFIED |
| **6** | Note for Teachers (1, 2, 3) | Non-assessed year-end topics, portfolio credit, textbook boxes not in exam | VERIFIED |
| **7–8** | Practicals (Experiments 1–14) | 14 lab experiments mapped to Units I, II, III, and IV for Internal Assessment | VERIFIED |
| **9** | Question Paper Design | Cognitive weightage: Knowledge (50%), Application (30%), Analysis/Evaluation (20%) | VERIFIED |

### Secondary Source: `NCERT_SCI_10_CH01` (`jesc101.pdf`)

| Page(s) | Section Heading | Extracted Content | Verification Verdict |
|:---:|---|---|:---:|
| **1–3** | Section 1.1: Chemical Equations | Daily life observations, word equations, skeletal equations | VERIFIED |
| **3–6** | Section 1.1.2: Balanced Chemical Equations | Law of conservation of mass, 7-step hit-and-trial balancing method | VERIFIED |
| **6–12** | Section 1.2: Types of Chemical Reactions | Combination (quicklime), decomposition (FeSO4, CaCO3, Pb(NO3)2, electrolysis of water, AgCl), displacement, double displacement, redox | VERIFIED |
| **12–13** | Section 1.3: Everyday Oxidation | Corrosion (rusting), rancidity, antioxidants, nitrogen flushing | VERIFIED |
| **13–16** | Summary, Exercises & Activities | Activities 1.1 to 1.11, end-of-chapter questions | VERIFIED |

---

## 4. Missing Source Documentation & Action Plan

The following NCERT textbook chapter files are not currently present in the local workspace:

| Chapter Number | Chapter Title | Expected NCERT File Name | Status | Impact on P0 | Remediation |
|:---:|---|---|:---:|---|---|
| 2 | Acids, Bases and Salts | `jesc102.pdf` | Missing | None on syllabus hierarchy; page refs pending | Ingest upon file addition |
| 3 | Metals and Non-Metals | `jesc103.pdf` | Missing | None on syllabus hierarchy; page refs pending | Ingest upon file addition |
| 4 | Carbon and Its Compounds | `jesc104.pdf` | Missing | None on syllabus hierarchy; page refs pending | Ingest upon file addition |
| 5 | Life Processes | `jesc105.pdf` | Missing | None on syllabus hierarchy; page refs pending | Ingest upon file addition |
| 6 | Control and Coordination | `jesc106.pdf` | Missing | None on syllabus hierarchy; page refs pending | Ingest upon file addition |
| 7 | How Do Organisms Reproduce? | `jesc107.pdf` | Missing | None on syllabus hierarchy; page refs pending | Ingest upon file addition |
| 8 | Heredity | `jesc108.pdf` | Missing | None on syllabus hierarchy; page refs pending | Ingest upon file addition |
| 9 | Light – Reflection and Refraction | `jesc109.pdf` | Missing | None on syllabus hierarchy; page refs pending | Ingest upon file addition |
| 10 | The Human Eye and the Colourful World | `jesc110.pdf` | Missing | None on syllabus hierarchy; page refs pending | Ingest upon file addition |
| 11 | Electricity | `jesc111.pdf` | Missing | None on syllabus hierarchy; page refs pending | Ingest upon file addition |
| 12 | Magnetic Effects of Electric Current | `jesc112.pdf` | Missing | None on syllabus hierarchy; page refs pending | Ingest upon file addition |
| 13 | Our Environment | `jesc113.pdf` | Missing | None on syllabus hierarchy; page refs pending | Ingest upon file addition |

### Audit Policy Compliance
- **Zero Fabrication Policy:** Exact page numbers from the missing NCERT textbook PDFs have deliberately **not been invented**.
- **Curriculum Grounding:** Every chapter title and syllabus-level topic is 100% verified against `Science_SecP1_2026-27.pdf`.
- **Pending Flag:** Additional textbook-level extraction for Chapters 2–13 is marked as `PENDING_TEXTBOOK_INGEST` in metadata.

---
*Report certified by P0 Source Document Management Service.*