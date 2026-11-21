# P1 — Concept Graph Specification

**Project:** Adaptive Exam-Prep Tutor with a Learner Model  
**Curriculum:** CBSE Class 10 Science (Subject Code 086)  
**Academic Session:** 2026–27  
**Phase:** P1 — Concept Graph Engine  
**Status:** **ACTIVE & OPERATIONAL**  
**Document Version:** 1.0.0  

---

## 1. Domain Definition & Purpose

The **Concept Graph Engine** provides the foundational cognitive knowledge structure for the Adaptive Exam-Prep Tutor. Unlike superficial question-answering tools, this system models the atomic components of understanding, their pedagogical dependencies, hierarchical affiliations, and curricular alignments.

The concept graph serves as the substrate for future phases:
- **Diagnostic Assessment (P2):** Formulating calibrated probes targeting specific concept nodes.
- **Learner Model (P3):** Tracking a student's latent mastery state (e.g., via Bayesian Knowledge Tracing or DINA models) across the graph.
- **Adaptive Question Generation (P5):** Selecting questions tailored to frontier concepts.
- **Misconception Detection (P7):** Identifying erroneous edges or missing foundational prerequisites.
- **Spaced Repetition (P8):** Scheduling targeted reviews along prerequisite learning pathways.

---

## 2. Graph Node Schema: `ConceptNode`

A **Concept Node** represents an atomic, teachable, assessable idea or skill.

### 2.1 Entity Attributes

| Attribute Name | Data Type | Constraints / Allowed Values | Description |
|---|---|---|---|
| `concept_id` | `TEXT` | Primary Key, `CPT-CHxx-yyy` | Deterministic, immutable concept identifier. |
| `name` | `TEXT` | Not Null | Human-readable title of the concept. |
| `canonical_name` | `TEXT` | Not Null, Unique, Lowercase Slug | Normalized slug preventing duplicate extraction (e.g. `chemical_reaction`). |
| `description` | `TEXT` | Not Null | Comprehensive pedagogical definition grounded in the textbook. |
| `chapter_id` | `TEXT` | Foreign Key `chapters(chapter_id)` | Parent textbook chapter ID (e.g. `CH-01`). |
| `topic_id` | `TEXT` | Foreign Key `topics(topic_id)` | Parent topic subdivision (e.g. `CH01-T01`). |
| `subtopic_id` | `TEXT` | Nullable, Foreign Key `subtopics` | Fine-grained subtopic reference (e.g. `CH01-T01-S01`). |
| `concept_type` | `TEXT` | `FOUNDATIONAL`, `CORE`, `APPLIED`, `PRACTICAL`, `EXTENDED` | Pedagogical role of the concept. |
| `difficulty_level` | `TEXT` | Nullable, `EASY`, `MEDIUM`, `HARD`, `UNCLASSIFIED` | Preliminary assessment complexity rubric. |
| `learning_objective`| `TEXT` | Nullable | Specific behavioral competency expected from the student. |
| `source_status` | `TEXT` | `SOURCE_DERIVED`, `CURRICULUM_SYNTHESIZED`, `INFERRED` | Origin of the concept entity. |
| `verification_status`| `TEXT` | `VERIFIED`, `SOURCE_VERIFIED`, `PENDING_VERIFICATION`, `HUMAN_REVIEW_REQUIRED`, `UNVERIFIED` | Traceability verification state. |
| `metadata_json` | `TEXT` | JSON Object | Arbitrary domain or assessment metadata. |
| `created_at` | `TIMESTAMP` | Default `CURRENT_TIMESTAMP` | System creation timestamp. |
| `updated_at` | `TIMESTAMP` | Default `CURRENT_TIMESTAMP` | Last updated timestamp. |

### 2.2 Concept Types Defined

1. **`FOUNDATIONAL`:** Core prerequisite principles without which subsequent chapter content cannot be interpreted (e.g., *Law of Conservation of Mass*).
2. **`CORE`:** Primary theoretical and procedural knowledge mandated for board examinations (e.g., *Balanced Chemical Equations*, *Combination Reactions*).
3. **`APPLIED`:** Real-world, industrial, or physiological manifestations (e.g., *Corrosion*, *Rancidity*, *Respiration as Exothermic*).
4. **`PRACTICAL`:** Laboratory experiments, observations, and procedural protocols (e.g., *Electrolysis of Water*, *Balancing via Hit-and-Trial*).
5. **`EXTENDED`:** Formative or extension modules identified in CBSE curriculum for internal assessment (e.g., *Early Attempts at Periodic Classification*).

---

## 3. Graph Edge Schema: `ConceptEdge`

A **Concept Edge** establishes a directed, typed semantic relationship between entities.

### 3.1 Entity Attributes

| Attribute Name | Data Type | Constraints / Allowed Values | Description |
|---|---|---|---|
| `edge_id` | `TEXT` | Primary Key, `EDGE-{src}-{type}-{tgt}` | Deterministic relationship identifier. |
| `source_concept_id` | `TEXT` | Foreign Key `concepts(concept_id)` | Originating concept node. |
| `target_concept_id` | `TEXT` | Not Null | Destination node (`concept_id` or `outcome_id`). |
| `relationship_type` | `TEXT` | `PREREQUISITE_OF`, `PART_OF`, `MAPS_TO`, `SUPPORTS_LEARNING_OUTCOME`, `RELATED_TO` | Typed relationship classification. |
| `description` | `TEXT` | Nullable | Pedagogical rationale justifying this edge. |
| `confidence` | `REAL` | Range `0.0 <= confidence <= 1.0` | Algorithmic or manual confidence metric. |
| `verification_status`| `TEXT` | Verification Status Enum | Verification audit state. |
| `source_provenance_json` | `TEXT` | JSON Object | Citation context supporting this edge. |
| `created_at` | `TIMESTAMP` | Default `CURRENT_TIMESTAMP` | Record creation timestamp. |

### 3.2 Relationship Types Defined

- **`PREREQUISITE_OF`:** Directed dependency ($u \rightarrow v$) signifying concept $u$ must be comprehended before concept $v$ can be acquired. **Strictly constrained by Directed Acyclic Graph (DAG) rules.**
- **`PART_OF`:** Hierarchical inclusion where $u$ is a constituent sub-concept or exemplar of $v$ (e.g., *Thermal Decomposition* `PART_OF` *Decomposition Reaction*).
- **`MAPS_TO`:** Curriculum mapping or semantic equivalence across curricula.
- **`SUPPORTS_LEARNING_OUTCOME`:** Connects a concept node to an official CBSE Learning Outcome (e.g., *Balanced Chemical Equation* $\rightarrow$ `LO-C1.3`).
- **`RELATED_TO`:** Lateral, contextual, or analogical association (e.g., *Exothermic Reactions* `RELATED_TO` *Endothermic Reactions*). **Explicitly exempt from DAG acyclicity constraints.**

---

## 4. Provenance Citation Schema: `ConceptProvenance`

Every concept and relationship derived from primary texts preserves forensic traceability.

### 4.1 Provenance Attributes

| Field | Type | Description |
|---|---|---|
| `provenance_id` | `TEXT PRIMARY KEY` | Deterministic citation ID (e.g. `PROV-CH01-001-01`). |
| `concept_id` | `TEXT REFERENCES concepts` | Target concept identifier. |
| `source_document_id` | `TEXT REFERENCES source_documents` | Registered document ID (e.g. `NCERT_SCI_10_CH01`). |
| `source_filename` | `TEXT` | Source filename (e.g. `jesc101.pdf`). |
| `page_number` | `INTEGER` | Exact 1-indexed page number in the source PDF. |
| `section_heading` | `TEXT` | Section title (e.g. `1.1.2 Balanced Chemical Equations`). |
| `extraction_method` | `TEXT` | `NATIVE_PDF_PARSE`, `BODHAN_OCR`, `LLM_ASSISTED_EXTRACTION`, `CURRICULUM_AUDIT`. |
| `confidence` | `REAL` | Confidence score (1.0 for manual/curriculum audit, float for model). |
| `verification_status`| `TEXT` | `SOURCE_VERIFIED`, `PENDING_VERIFICATION`, `UNVERIFIED`. |
| `verbatim_text` | `TEXT` | Exact sentence or excerpt from the official text. |

---

## 5. Mathematical & Graph Integrity Rules

The Concept Graph Engine enforces 8 formal mathematical and relational invariants:

```
[ Rule CG-01: Canonical Uniqueness ] ──> Unique slugs & IDs; deterministic merging.
[ Rule CG-02: Parent Integrity ]    ──> Valid foreign keys to chapters, topics, subtopics.
[ Rule CG-03: Edge Referential Integrity ] ──> Source & target nodes must exist.
[ Rule CG-04: Edge Uniqueness ]     ──> Unique (source, target, type) index in SQLite.
[ Rule CG-05: Strict Prerequisite DAG ] ──> Prerequisite subgraph has ZERO cycles.
[ Rule CG-06: Non-DAG Exemptions ]  ──> RELATED_TO edges excluded from acyclic checks.
[ Rule CG-07: Provenance Mandatory ]──> Verified concepts must have valid citations.
[ Rule CG-08: Cross-Topic Continuity]──> Inter-topic learning progressions verified.
```

1. **Cycle Detection Algorithm:** Depth-First Search with recursion stack tracking. When a back-edge is encountered, the algorithm reconstructs the exact cycle loop ($u \rightarrow \dots \rightarrow v \rightarrow u$).
2. **Topological Ordering Algorithm:** Kahn's algorithm computing in-degrees across `PREREQUISITE_OF` edges. Guarantees that every prerequisite precedes all of its dependent concepts.
3. **Ancestor / Descendant Traversal:** Breadth-first search along directed and reverse adjacency graphs, returning ordered prerequisite dependency chains.

---

## 6. Architectural Decisions (ADRs)

- **ADR-P1-01: SQLite Relational Backing with Strict Foreign Keys:** Rather than introducing a heavyweight graph database (e.g., Neo4j), SQLite provides zero-dependency transactional durability, ACID guarantees, and strict foreign key referential integrity matching the P0 architecture.
- **ADR-P1-02: Isolated In-Memory Graph Algorithms:** Cycle detection, topological sort, and reachability traversals execute in Python memory on adjacency lists constructed from SQLite queries, ensuring sub-millisecond query performance.
- **ADR-P1-03: Zero Live API Consumption in Automated Tests:** LLM-assisted candidate extraction features a mockable injection interface, enabling 100% deterministic testing without burning cloud API credits.
