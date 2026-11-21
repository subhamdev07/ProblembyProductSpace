"""
Concept Graph Domain Models
Defines ConceptNode, ConceptEdge, ConceptProvenance, and supporting Enums
for P1 — Concept Graph Engine.
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, model_validator


class ConceptType(str, Enum):
    """
    Pedagogical role of the concept.
    - FOUNDATIONAL: Essential prerequisite underlying higher-level concepts.
    - CORE: Central curriculum learning unit required for examination.
    - APPLIED: Practical or everyday manifestation of core concepts.
    - PRACTICAL: Laboratory activity, experiment, or observation.
    - EXTENDED: Formative/extension concept outside core examination.
    """
    FOUNDATIONAL = "FOUNDATIONAL"
    CORE = "CORE"
    APPLIED = "APPLIED"
    PRACTICAL = "PRACTICAL"
    EXTENDED = "EXTENDED"


class RelationshipType(str, Enum):
    """
    Typed relationship between concepts or curriculum nodes.
    - PREREQUISITE_OF: source concept must be learned before target concept.
    - PART_OF: source concept is a component or sub-concept of target.
    - MAPS_TO: semantic equivalence or curriculum mapping.
    - SUPPORTS_LEARNING_OUTCOME: concept directly fulfills a learning outcome.
    - RELATED_TO: lateral association or contextual relevance (non-DAG).
    """
    PREREQUISITE_OF = "PREREQUISITE_OF"
    PART_OF = "PART_OF"
    MAPS_TO = "MAPS_TO"
    SUPPORTS_LEARNING_OUTCOME = "SUPPORTS_LEARNING_OUTCOME"
    RELATED_TO = "RELATED_TO"


class ConceptVerificationStatus(str, Enum):
    """
    Verification status of a concept node or relationship edge.
    """
    VERIFIED = "VERIFIED"
    SOURCE_VERIFIED = "SOURCE_VERIFIED"
    PENDING_VERIFICATION = "PENDING_VERIFICATION"
    HUMAN_REVIEW_REQUIRED = "HUMAN_REVIEW_REQUIRED"
    UNVERIFIED = "UNVERIFIED"


class SourceStatus(str, Enum):
    """
    Origin of the concept within the curriculum or textbook.
    - SOURCE_DERIVED: Extracted directly from primary textbook (e.g. NCERT).
    - CURRICULUM_SYNTHESIZED: Derived from CBSE syllabus statements.
    - INFERRED: Synthesized by LLM or curriculum analyst.
    """
    SOURCE_DERIVED = "SOURCE_DERIVED"
    CURRICULUM_SYNTHESIZED = "CURRICULUM_SYNTHESIZED"
    INFERRED = "INFERRED"


class ConceptProvenance(BaseModel):
    """
    Fine-grained source citation and provenance record for a concept or edge.
    """
    provenance_id: str = Field(..., description="Unique provenance record ID")
    concept_id: str = Field(..., description="Target concept identifier")
    source_document_id: str = Field(..., description="Reference to source_documents.document_id")
    source_filename: str = Field(..., description="Source filename, e.g. 'jesc101.pdf'")
    page_number: Optional[int] = Field(None, description="Page number where concept appears in source")
    section_heading: Optional[str] = Field(None, description="Heading of the section containing concept")
    extraction_method: str = Field(..., description="Method used: NATIVE_PDF_PARSE, BODHAN_OCR, LLM_ASSISTED_EXTRACTION, etc.")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Extraction confidence score (0.0 to 1.0)")
    verification_status: ConceptVerificationStatus = Field(default=ConceptVerificationStatus.SOURCE_VERIFIED)
    verbatim_text: Optional[str] = Field(None, description="Verbatim quote or excerpt from the source")
    created_at: Optional[str] = None


class ConceptNode(BaseModel):
    """
    Atomic, assessable, teachable concept node in the Concept Graph.
    """
    concept_id: str = Field(..., description="Stable deterministic ID, e.g. 'CPT-CH01-001'")
    name: str = Field(..., description="Human-readable concept name")
    canonical_name: str = Field(..., description="Unique machine-readable identifier, e.g. 'chemical_reaction'")
    description: str = Field(..., description="Definitive pedagogical description of the concept")
    chapter_id: str = Field(..., description="Parent chapter ID, e.g. 'CH-01'")
    topic_id: str = Field(..., description="Parent topic ID, e.g. 'CH01-T01'")
    subtopic_id: Optional[str] = Field(None, description="Parent subtopic ID, e.g. 'CH01-T01-S01'")
    concept_type: ConceptType = Field(default=ConceptType.CORE)
    difficulty_level: Optional[str] = Field(None, description="Difficulty classification: EASY, MEDIUM, HARD, UNCLASSIFIED")
    learning_objective: Optional[str] = Field(None, description="Specific student understanding expected")
    source_status: SourceStatus = Field(default=SourceStatus.SOURCE_DERIVED)
    verification_status: ConceptVerificationStatus = Field(default=ConceptVerificationStatus.VERIFIED)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    provenance_records: List[ConceptProvenance] = Field(default_factory=list)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    @model_validator(mode="after")
    def validate_difficulty(self):
        if self.difficulty_level is not None:
            valid_levels = {"EASY", "MEDIUM", "HARD", "UNCLASSIFIED"}
            if self.difficulty_level.upper() not in valid_levels:
                raise ValueError(f"Invalid difficulty_level: '{self.difficulty_level}'. Must be one of {valid_levels}")
        return self


class ConceptEdge(BaseModel):
    """
    Typed relationship edge connecting concepts or learning outcomes in the graph.
    """
    edge_id: str = Field(..., description="Deterministic unique edge ID, e.g. 'EDGE-CPT01-PREREQ-CPT02'")
    source_concept_id: str = Field(..., description="Source concept ID")
    target_concept_id: str = Field(..., description="Target concept ID or learning outcome ID")
    relationship_type: RelationshipType = Field(..., description="Relationship type enum")
    description: Optional[str] = Field(None, description="Pedagogical rationale for this relationship")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence score")
    verification_status: ConceptVerificationStatus = Field(default=ConceptVerificationStatus.VERIFIED)
    source_provenance: Optional[Dict[str, Any]] = Field(default=None, description="Provenance metadata for the edge")
    created_at: Optional[str] = None

    @model_validator(mode="after")
    def validate_self_loop(self):
        if self.source_concept_id == self.target_concept_id:
            raise ValueError(f"Self-loops are forbidden in concept graph edges: {self.source_concept_id}")
        return self
