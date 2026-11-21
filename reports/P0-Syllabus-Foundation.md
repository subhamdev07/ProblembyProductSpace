# P0 — Syllabus Foundation Master Specification

**Project:** Adaptive Exam-Prep Tutor with a Learner Model  
**Curriculum:** CBSE Class 10 Science (Subject Code 086)  
**Academic Session:** 2026–27  
**Phase:** P0 — Syllabus Foundation (Completed)  

---

## 1. Objectives & Scope Governance

The objective of P0 is to establish an unshakeable, mathematically consistent, source-traceable curriculum foundation for CBSE Class 10 Science.

### In-Scope Deliverables (P0 Completed):
- Formal representation of Academic Session 2026–27, Subject (086), and Curriculum.
- Strict preservation of the 5-layer hierarchy: `Academic Session -> Subject -> Unit -> Chapter -> Topic -> Subtopic`.
- Complete registration of all **5 CBSE Units** and all **13 NCERT Textbook Chapters**.
- Unit-to-Chapter relational mappings with official mark allocations.
- Comprehensive topic and subtopic extraction with assessment classifications (`SUMMATIVE`, `FORMATIVE`, `NOT_IN_CURRENT_SCOPE`).
- Official Learning Outcome registry linking Curricular Goals (CG 1–CG 8) and Competencies (C 1.1–C 8.2) to chapters.
- Relational SQLite database with foreign key constraints, unique indexes, and ACID guarantees.
- 12-rule Curriculum Validation Engine.

### Out-of-Scope Modules (Strictly Deferred to Future Phases):
- Concept Graph & Prerequisite DAGs (P1)
- Diagnostic Assessment Engine & Item Response Calibration (P2)
- Bayesian / Knowledge Tracing Learner Models (P3)
- Adaptive Question Generation (P4)
- Spaced Repetition Scheduling (P5)
- Teacher / Admin Analytics Dashboard (P6)

---

## 2. Curriculum Architecture & Hierarchy

```
Academic Session (2026–27)
    └── Class 10
        └── Science (Code 086)
            ├── Unit I: Chemical Substances - Nature and Behaviour [25 Marks]
            │   ├── Chapter 1: Chemical Reactions and Equations
            │   ├── Chapter 2: Acids, Bases and Salts
            │   ├── Chapter 3: Metals and Non-Metals
            │   └── Chapter 4: Carbon and Its Compounds
            │       └── [Formative Topic: Periodic Classification of Elements]
            ├── Unit II: World of Living [25 Marks]
            │   ├── Chapter 5: Life Processes
            │   ├── Chapter 6: Control and Coordination
            │   ├── Chapter 7: How Do Organisms Reproduce?
            │   └── Chapter 8: Heredity
            │       └── [Formative Topic: Evolution]
            ├── Unit III: Natural Phenomena [12 Marks]
            │   ├── Chapter 9: Light – Reflection and Refraction
            │   └── Chapter 10: The Human Eye and the Colourful World
            │       └── [Excluded Scope: Colour of Sun at Sunrise/Sunset]
            ├── Unit IV: Effects of Current [13 Marks]
            │   ├── Chapter 11: Electricity
            │   └── Chapter 12: Magnetic Effects of Electric Current
            │       └── [Formative Topic: Electric Motor, Induction, Generator]
            └── Unit V: Natural Resources [05 Marks]
                └── Chapter 13: Our Environment
```

---

## 3. Unit-Wise Master Chapter & Mark Allocation Matrix

| Unit ID | Unit Title | Theme | Board Marks | Mapped Chapter ID | Chapter Number | Official Chapter Name | Assessment Status |
|---|---|---|:---:|---|:---:|---|:---:|
| `UNIT-01` | Chemical Substances - Nature and Behaviour | Materials | **25** | `CH-01` | 1 | Chemical Reactions and Equations | `SUMMATIVE` |
| `UNIT-01` | Chemical Substances - Nature and Behaviour | Materials | **25** | `CH-02` | 2 | Acids, Bases and Salts | `SUMMATIVE` |
| `UNIT-01` | Chemical Substances - Nature and Behaviour | Materials | **25** | `CH-03` | 3 | Metals and Non-Metals | `SUMMATIVE` |
| `UNIT-01` | Chemical Substances - Nature and Behaviour | Materials | **25** | `CH-04` | 4 | Carbon and Its Compounds | `SUMMATIVE` |
| `UNIT-02` | World of Living | The World of the Living | **25** | `CH-05` | 5 | Life Processes | `SUMMATIVE` |
| `UNIT-02` | World of Living | The World of the Living | **25** | `CH-06` | 6 | Control and Coordination | `SUMMATIVE` |
| `UNIT-02` | World of Living | The World of the Living | **25** | `CH-07` | 7 | How Do Organisms Reproduce? | `SUMMATIVE` |
| `UNIT-02` | World of Living | The World of the Living | **25** | `CH-08` | 8 | Heredity | `SUMMATIVE` |
| `UNIT-03` | Natural Phenomena | Natural Phenomena | **12** | `CH-09` | 9 | Light – Reflection and Refraction | `SUMMATIVE` |
| `UNIT-03` | Natural Phenomena | Natural Phenomena | **12** | `CH-10` | 10 | The Human Eye and the Colourful World | `SUMMATIVE` |
| `UNIT-04` | Effects of Current | How Things Work | **13** | `CH-11` | 11 | Electricity | `SUMMATIVE` |
| `UNIT-04` | Effects of Current | How Things Work | **13** | `CH-12` | 12 | Magnetic Effects of Electric Current | `SUMMATIVE` |
| `UNIT-05` | Natural Resources | Natural Resources | **5** | `CH-13` | 13 | Our Environment | `SUMMATIVE` |

**Total Board Theory Marks:** 80 Marks  
**Internal Assessment:** 20 Marks  
**Grand Total:** 100 Marks  

---

## 4. Extracted Topics by Chapter

### I. Chemical Substances - Nature and Behaviour (25 Marks)

#### Chapter 1: Chemical Reactions and Equations (`CH-01`)
- **Assessment Status:** `SUMMATIVE`
- **Verification Status:** `VERIFIED`

| Topic ID | Topic Name | Status | Verified Source | Subtopics Count |
|---|---|:---:|---|:---:|
| `CH01-T01` | Chemical Equations and Balancing | `SUMMATIVE` | CBSE_SCI_10_2026_27 (p.4) | 3 |
| `CH01-T02` | Types of Chemical Reactions | `SUMMATIVE` | CBSE_SCI_10_2026_27 (p.4) | 5 |
| `CH01-T03` | Oxidation and Reduction | `SUMMATIVE` | CBSE_SCI_10_2026_27 (p.4) | 2 |
| `CH01-T04` | Periodic Classification of Elements (Formative Learning) | `FORMATIVE` | CBSE_SCI_10_2026_27 (p.4) | 3 |

#### Chapter 2: Acids, Bases and Salts (`CH-02`)
- **Assessment Status:** `SUMMATIVE`
- **Verification Status:** `VERIFIED`

| Topic ID | Topic Name | Status | Verified Source | Subtopics Count |
|---|---|:---:|---|:---:|
| `CH02-T01` | Acids and Bases - Nature and Indicators | `SUMMATIVE` | CBSE_SCI_10_2026_27 (p.4) | 2 |
| `CH02-T02` | Chemical Properties of Acids and Bases | `SUMMATIVE` | CBSE_SCI_10_2026_27 (p.4) | 3 |
| `CH02-T03` | Concept of pH Scale and Everyday Applications | `SUMMATIVE` | CBSE_SCI_10_2026_27 (p.4) | 2 |
| `CH02-T04` | Preparation, Properties and Uses of Important Salts | `SUMMATIVE` | CBSE_SCI_10_2026_27 (p.4) | 5 |

#### Chapter 3: Metals and Non-Metals (`CH-03`)
- **Assessment Status:** `SUMMATIVE`
- **Verification Status:** `VERIFIED`

| Topic ID | Topic Name | Status | Verified Source | Subtopics Count |
|---|---|:---:|---|:---:|
| `CH03-T01` | Physical and Chemical Properties of Metals and Non-Metals | `SUMMATIVE` | CBSE_SCI_10_2026_27 (p.5) | 2 |
| `CH03-T02` | Reactivity Series of Metals | `SUMMATIVE` | CBSE_SCI_10_2026_27 (p.5) | 1 |
| `CH03-T03` | Formation and Properties of Ionic Compounds | `SUMMATIVE` | CBSE_SCI_10_2026_27 (p.5) | 2 |
| `CH03-T04` | Basic Metallurgical Processes | `SUMMATIVE` | CBSE_SCI_10_2026_27 (p.5) | 2 |
| `CH03-T05` | Corrosion and Its Prevention | `SUMMATIVE` | CBSE_SCI_10_2026_27 (p.5) | 1 |

#### Chapter 4: Carbon and Its Compounds (`CH-04`)
- **Assessment Status:** `SUMMATIVE`
- **Verification Status:** `VERIFIED`

| Topic ID | Topic Name | Status | Verified Source | Subtopics Count |
|---|---|:---:|---|:---:|
| `CH04-T01` | Covalent Bonding and Versatile Nature of Carbon | `SUMMATIVE` | CBSE_SCI_10_2026_27 (p.5) | 2 |
| `CH04-T02` | Saturated and Unsaturated Hydrocarbons and Homologous Series | `SUMMATIVE` | CBSE_SCI_10_2026_27 (p.5) | 2 |
| `CH04-T03` | Nomenclature of Carbon Compounds Containing Functional Groups | `SUMMATIVE` | CBSE_SCI_10_2026_27 (p.5) | 1 |
| `CH04-T04` | Chemical Properties of Carbon Compounds | `SUMMATIVE` | CBSE_SCI_10_2026_27 (p.5) | 2 |
| `CH04-T05` | Ethanol and Ethanoic Acid | `SUMMATIVE` | CBSE_SCI_10_2026_27 (p.5) | 2 |
| `CH04-T06` | Soaps and Detergents | `SUMMATIVE` | CBSE_SCI_10_2026_27 (p.5) | 1 |

### II. World of Living (25 Marks)

#### Chapter 5: Life Processes (`CH-05`)
- **Assessment Status:** `SUMMATIVE`
- **Verification Status:** `VERIFIED`

| Topic ID | Topic Name | Status | Verified Source | Subtopics Count |
|---|---|:---:|---|:---:|
| `CH05-T01` | Concept of Living Beings and Maintenance Processes | `SUMMATIVE` | CBSE_SCI_10_2026_27 (p.5) | 1 |
| `CH05-T02` | Nutrition in Plants and Animals | `SUMMATIVE` | CBSE_SCI_10_2026_27 (p.5) | 3 |
| `CH05-T03` | Respiration in Plants and Animals | `SUMMATIVE` | CBSE_SCI_10_2026_27 (p.5) | 2 |
| `CH05-T04` | Transportation in Plants and Animals | `SUMMATIVE` | CBSE_SCI_10_2026_27 (p.5) | 3 |
| `CH05-T05` | Excretion in Plants and Animals | `SUMMATIVE` | CBSE_SCI_10_2026_27 (p.5) | 2 |

#### Chapter 6: Control and Coordination (`CH-06`)
- **Assessment Status:** `SUMMATIVE`
- **Verification Status:** `VERIFIED`

| Topic ID | Topic Name | Status | Verified Source | Subtopics Count |
|---|---|:---:|---|:---:|
| `CH06-T01` | Tropic Movements and Plant Hormones | `SUMMATIVE` | CBSE_SCI_10_2026_27 (p.5) | 2 |
| `CH06-T02` | Nervous System and Reflex Action in Animals | `SUMMATIVE` | CBSE_SCI_10_2026_27 (p.5) | 2 |
| `CH06-T03` | Human Brain and Voluntary/Involuntary Actions | `SUMMATIVE` | CBSE_SCI_10_2026_27 (p.5) | 1 |
| `CH06-T04` | Chemical Coordination: Animal Hormones | `SUMMATIVE` | CBSE_SCI_10_2026_27 (p.5) | 2 |

#### Chapter 7: How Do Organisms Reproduce? (`CH-07`)
- **Assessment Status:** `SUMMATIVE`
- **Verification Status:** `VERIFIED`

| Topic ID | Topic Name | Status | Verified Source | Subtopics Count |
|---|---|:---:|---|:---:|
| `CH07-T01` | Asexual Reproduction in Organisms | `SUMMATIVE` | CBSE_SCI_10_2026_27 (p.5) | 2 |
| `CH07-T02` | Sexual Reproduction in Flowering Plants | `SUMMATIVE` | CBSE_SCI_10_2026_27 (p.5) | 2 |
| `CH07-T03` | Reproduction in Human Beings | `SUMMATIVE` | CBSE_SCI_10_2026_27 (p.5) | 2 |
| `CH07-T04` | Reproductive Health and Family Planning | `SUMMATIVE` | CBSE_SCI_10_2026_27 (p.5) | 2 |

#### Chapter 8: Heredity (`CH-08`)
- **Assessment Status:** `SUMMATIVE`
- **Verification Status:** `VERIFIED`

| Topic ID | Topic Name | Status | Verified Source | Subtopics Count |
|---|---|:---:|---|:---:|
| `CH08-T01` | Heredity and Mendel's Laws of Inheritance | `SUMMATIVE` | CBSE_SCI_10_2026_27 (p.5) | 2 |
| `CH08-T02` | Sex Determination in Human Beings | `SUMMATIVE` | CBSE_SCI_10_2026_27 (p.5) | 1 |
| `CH08-T03` | Evolution and Speciation (Formative Learning) | `FORMATIVE` | CBSE_SCI_10_2026_27 (p.5) | 3 |

### III. Natural Phenomena (12 Marks)

#### Chapter 9: Light – Reflection and Refraction (`CH-09`)
- **Assessment Status:** `SUMMATIVE`
- **Verification Status:** `VERIFIED`

| Topic ID | Topic Name | Status | Verified Source | Subtopics Count |
|---|---|:---:|---|:---:|
| `CH09-T01` | Reflection of Light by Spherical Mirrors | `SUMMATIVE` | CBSE_SCI_10_2026_27 (p.5) | 2 |
| `CH09-T02` | Mirror Formula and Magnification | `SUMMATIVE` | CBSE_SCI_10_2026_27 (p.5) | 2 |
| `CH09-T03` | Refraction of Light and Refractive Index | `SUMMATIVE` | CBSE_SCI_10_2026_27 (p.5) | 2 |
| `CH09-T04` | Refraction by Spherical Lenses, Lens Formula and Power | `SUMMATIVE` | CBSE_SCI_10_2026_27 (p.5) | 2 |

#### Chapter 10: The Human Eye and the Colourful World (`CH-10`)
- **Assessment Status:** `SUMMATIVE`
- **Verification Status:** `VERIFIED`

| Topic ID | Topic Name | Status | Verified Source | Subtopics Count |
|---|---|:---:|---|:---:|
| `CH10-T01` | Human Eye and Defects of Vision | `SUMMATIVE` | CBSE_SCI_10_2026_27 (p.6) | 2 |
| `CH10-T02` | Prism Refraction and Dispersion of Light | `SUMMATIVE` | CBSE_SCI_10_2026_27 (p.6) | 2 |
| `CH10-T03` | Atmospheric Refraction and Scattering of Light | `SUMMATIVE` | CBSE_SCI_10_2026_27 (p.6) | 2 |
| `CH10-T04` | Colour of the Sun at Sunrise and Sunset (Excluded Scope) | `NOT_IN_CURRENT_SCOPE` | CBSE_SCI_10_2026_27 (p.6) | 1 |

### IV. Effects of Current (13 Marks)

#### Chapter 11: Electricity (`CH-11`)
- **Assessment Status:** `SUMMATIVE`
- **Verification Status:** `VERIFIED`

| Topic ID | Topic Name | Status | Verified Source | Subtopics Count |
|---|---|:---:|---|:---:|
| `CH11-T01` | Electric Current, Potential Difference and Ohm's Law | `SUMMATIVE` | CBSE_SCI_10_2026_27 (p.6) | 2 |
| `CH11-T02` | Resistance and Resistivity | `SUMMATIVE` | CBSE_SCI_10_2026_27 (p.6) | 1 |
| `CH11-T03` | Series and Parallel Combinations of Resistors | `SUMMATIVE` | CBSE_SCI_10_2026_27 (p.6) | 2 |
| `CH11-T04` | Heating Effect of Electric Current | `SUMMATIVE` | CBSE_SCI_10_2026_27 (p.6) | 2 |
| `CH11-T05` | Electric Power and Commercial Energy | `SUMMATIVE` | CBSE_SCI_10_2026_27 (p.6) | 2 |

#### Chapter 12: Magnetic Effects of Electric Current (`CH-12`)
- **Assessment Status:** `SUMMATIVE`
- **Verification Status:** `VERIFIED`

| Topic ID | Topic Name | Status | Verified Source | Subtopics Count |
|---|---|:---:|---|:---:|
| `CH12-T01` | Magnetic Field and Field Lines | `SUMMATIVE` | CBSE_SCI_10_2026_27 (p.6) | 1 |
| `CH12-T02` | Magnetic Field Due to Current Carrying Conductors | `SUMMATIVE` | CBSE_SCI_10_2026_27 (p.6) | 2 |
| `CH12-T03` | Force on Current-Carrying Conductor in Magnetic Field | `SUMMATIVE` | CBSE_SCI_10_2026_27 (p.6) | 1 |
| `CH12-T04` | Direct and Alternating Current and Domestic Electric Circuits | `SUMMATIVE` | CBSE_SCI_10_2026_27 (p.6) | 2 |
| `CH12-T05` | Electric Motor, Electromagnetic Induction and Generator (Formative Learning) | `FORMATIVE` | CBSE_SCI_10_2026_27 (p.6) | 2 |

### V. Natural Resources (5 Marks)

#### Chapter 13: Our Environment (`CH-13`)
- **Assessment Status:** `SUMMATIVE`
- **Verification Status:** `VERIFIED`

| Topic ID | Topic Name | Status | Verified Source | Subtopics Count |
|---|---|:---:|---|:---:|
| `CH13-T01` | Ecosystem and Food Chains | `SUMMATIVE` | CBSE_SCI_10_2026_27 (p.6) | 2 |
| `CH13-T02` | Environmental Problems and Ozone Layer Depletion | `SUMMATIVE` | CBSE_SCI_10_2026_27 (p.6) | 2 |
| `CH13-T03` | Waste Production and Solutions | `SUMMATIVE` | CBSE_SCI_10_2026_27 (p.6) | 2 |

---

## 5. Assessment Classifications & Edge Case Governance

Every curriculum entity carries an explicit assessment classification:

1. **`SUMMATIVE` (Board Examination Scope):**
   - Assessed in the 80-mark year-end board examination.
   - Covers core theoretical and numerical topics across all 13 chapters.
2. **`FORMATIVE` (School-Based & Internal Assessment Scope):**
   - **Periodic Classification of Elements (Unit I / Ch 1-4):** Döbereiner's Triads, Newlands' Law of Octaves, Mendeleev's Periodic Table, Modern Periodic Table. Preserved in curriculum for portfolio/internal credit.
   - **Evolution (Unit II / Ch 8):** Acquired/inherited traits, speciation, evolutionary relationships, fossils, human evolution. Retained for conceptual continuity without exam stress.
   - **Electric Motor, Electromagnetic Induction, and Electric Generator (Unit IV / Ch 12):** Assessed formatively via practical projects and internal assignments.
3. **`NOT_IN_CURRENT_SCOPE` (Explicitly Excluded by CBSE):**
   - **Colour of the Sun at Sunrise and Sunset (Chapter 10):** Explicitly excluded by CBSE in the syllabus: *(excluding colour of the sun at sunrise and sunset)*.
   - **Information Boxes in NCERT Textbooks:** As stated in CBSE Note 3, information in boxes across NCERT textbooks is intended for conceptual clarity only and is excluded from the year-end examination.
4. **`PENDING_VERIFICATION`:**
   - Used as a safeguard for any non-authoritative curriculum proposals.

---

## 6. Learning Outcome Registry

The curriculum foundation registers Curricular Goals and Competencies defined in the official curriculum:

| Outcome ID | Competency Code | Associated Chapter | Curricular Goal | Capability Statement | Provenance |
|---|:---:|---|---|---|:---:|
| `LO-C1.1` | `C 1.1` | `CH-01` | CG 1 | Describes classification of elements in the Periodic Table, and explains how compounds (including carbon compounds) are formed based on the atomic structure (Bohr’s model) and properties (valency). | `OFFICIAL` |
| `LO-C1.3` | `C 1.3` | `CH-01` | CG 1 | Describes and represents chemical interactions and changes using symbols and chemical equations (acid and base, metal and non-metal, reversible and irreversible). | `OFFICIAL` |
| `LO-C1.2` | `C 1.2` | `CH-02` | CG 1 | Investigates the nature and properties of chemical substances (distillation, crystallisation, chromatography, centrifugation, types and properties of mixtures, solutions, colloids, and suspensions). | `OFFICIAL` |
| `LO-CH04-C1.1` | `C 1.1 (Carbon)` | `CH-04` | CG 1 | Explains covalent bond formation, tetravalency, and catenation properties that allow carbon to form versatile saturated and unsaturated compounds and functional groups. | `OFFICIAL` |
| `LO-C3.2` | `C 3.2` | `CH-05` | CG 3 | Analyses similarities and differences in the life processes involved in nutrition (photosynthesis in plants; digestion in animals), transport (transport of water in plants; circulation in animals), exchange of materials (respiration and excretion), and reproduction. | `OFFICIAL` |
| `LO-C3.1` | `C 3.1` | `CH-06` | CG 3 | Explains cellular and tissue mechanisms in maintaining coordination, transmission of electrical and chemical impulses across neurons, and hormone-mediated physiological responses. | `INFERRED` |
| `LO-CH07-C3.2` | `C 3.2 (Reproduction)` | `CH-07` | CG 3 | Compares asexual and sexual reproduction strategies in plants and animals and evaluates human reproductive health requirements. | `OFFICIAL` |
| `LO-C3.3` | `C 3.3` | `CH-08` | CG 3 | Describes the mechanisms of heredity (in terms of DNA, genes, chromosomes) and variation (as changes in the sequence of DNA). | `OFFICIAL` |
| `LO-C4.4` | `C 4.4` | `CH-08` | CG 4 | Analyses patterns of inheritance of traits in terms of Mendel’s laws and its consequences at a population level (using models and/or simulations). | `OFFICIAL` |
| `LO-C4.5` | `C 4.5` | `CH-08` | CG 4 | Analyses evidences of biological evolution demonstrating the consequences of the process of natural selection in terms of changes in allele frequency in population, structure, and function of organisms. | `OFFICIAL` |
| `LO-C2.3` | `C 2.3` | `CH-09` | CG 2 | Manipulates the position of object and properties of lenses (focus, centre of curvature) to observe image characteristics and correspondence with a ray diagram, and extends this understanding to a combination of lenses (telescope, microscope). | `OFFICIAL` |
| `LO-CH10-C2.3` | `C 2.3 (Vision)` | `CH-10` | CG 2 | Applies lens principles to describe the functioning of the human crystalline lens, identifies visual defects, and calculates corrective lens powers. | `INFERRED` |
| `LO-C2.4` | `C 2.4` | `CH-11` | CG 2 | Manipulates and analyses different characteristics of the circuit (current, voltage, resistance) and mathematises their relationship (Ohm’s law), and applies it to everyday usage (electricity bill, short circuit, safety measures). | `OFFICIAL` |
| `LO-CH12-C8.1` | `C 8.1 (Electromagnetism)` | `CH-12` | CG 8 | Develops accurate physical and directional vector models (Right-Hand Thumb Rule, Fleming’s Left-Hand Rule) to predict magnetic field lines and electromagnetic force directions. | `OFFICIAL` |
| `LO-C4.3` | `C 4.3` | `CH-13` | CG 4 | Analyses different levels of biological organisation from organisms to ecosystems and biomes along with interactions that take place at each level. | `OFFICIAL` |

---

## 7. Data Architecture & Relational Schema

The foundational data layer is implemented in SQLite with strict foreign key constraints and validated Pydantic models:

- `academic_sessions`: Stores academic session intervals.
- `subjects`: Stores domain parameters (Code: 086, Science).
- `curricula`: Root curriculum records.
- `units`: 5 CBSE Units with mark weightages and themes.
- `chapters`: 13 NCERT Chapters mapped to Units via foreign keys.
- `topics`: Sequential chapter subdivisions.
- `subtopics`: Granular pedagogical items.
- `learning_outcomes`: Explicit competency milestones with Bloom/taxonomy verbs.
- `source_documents`: Cryptographically fingerprinted primary sources (SHA-256).
- `curriculum_mappings`: Explicit directional graph bindings.

---
*Report generated by P0 Syllabus Foundation Engine.*