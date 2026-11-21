"""
Curriculum Hierarchy Models: Unit, Chapter, Topic, Subtopic
Strictly preserves the 5-layer hierarchy:
Academic Session -> Subject -> Unit -> Chapter -> Topic -> Subtopic
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from src.models.classification import AssessmentClassification, VerificationStatus
from src.models.source import SourceReference


class Unit(BaseModel):
    """
    Curriculum Grouping entity (e.g. Unit I: Chemical Substances - Nature and Behaviour).
    Units are thematic groupings carrying examination weightages (marks).
    UNITS ARE DISTINCT FROM TEXTBOOK CHAPTERS.
    """
    unit_id: str = Field(..., description="Unique Unit identifier, e.g. 'UNIT-01'")
    unit_number: str = Field(..., description="Roman numeral identifier, e.g. 'I'")
    name: str = Field(..., description="Unit title, e.g. 'Chemical Substances - Nature and Behaviour'")
    theme: Optional[str] = Field(None, description="Thematic category, e.g. 'Materials'")
    curriculum_id: str = Field(..., description="Parent curriculum reference")
    marks: Optional[int] = Field(None, description="Summative examination marks allocated to this unit")
    verification_status: VerificationStatus = Field(default=VerificationStatus.VERIFIED)
    source_reference: Optional[SourceReference] = None


class Chapter(BaseModel):
    """
    Textbook Chapter entity (e.g. Chapter 1: Chemical Reactions and Equations).
    Chapters correspond to standard pedagogical modules and textbook divisions.
    """
    chapter_id: str = Field(..., description="Unique Chapter ID, e.g. 'CH-01'")
    chapter_number: int = Field(..., description="Official Chapter number, 1 through 13")
    name: str = Field(..., description="Official textbook chapter title")
    unit_id: str = Field(..., description="Parent Unit ID (mapping chapter into curriculum unit)")
    curriculum_id: str = Field(..., description="Parent curriculum reference")
    assessment_status: AssessmentClassification = Field(default=AssessmentClassification.SUMMATIVE)
    verification_status: VerificationStatus = Field(default=VerificationStatus.VERIFIED)
    source_references: List[SourceReference] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Topic(BaseModel):
    """
    Topic entity representing an instructional sub-division of a Chapter.
    """
    topic_id: str = Field(..., description="Unique Topic ID, e.g. 'CH01-T01'")
    chapter_id: str = Field(..., description="Parent Chapter ID, e.g. 'CH-01'")
    name: str = Field(..., description="Topic title")
    sequence_order: int = Field(default=1, description="Order within chapter")
    description: Optional[str] = Field(None, description="Detailed scope or description of the topic")
    assessment_status: AssessmentClassification = Field(default=AssessmentClassification.SUMMATIVE)
    verification_status: VerificationStatus = Field(default=VerificationStatus.VERIFIED)
    source_references: List[SourceReference] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Subtopic(BaseModel):
    """
    Subtopic entity representing granular content elements within a Topic.
    """
    subtopic_id: str = Field(..., description="Unique Subtopic ID, e.g. 'CH01-T01-S01'")
    topic_id: str = Field(..., description="Parent Topic ID")
    name: str = Field(..., description="Subtopic title")
    sequence_order: int = Field(default=1, description="Order within topic")
    description: Optional[str] = Field(None, description="Scope notes or pedagogical focus")
    assessment_status: AssessmentClassification = Field(default=AssessmentClassification.SUMMATIVE)
    verification_status: VerificationStatus = Field(default=VerificationStatus.VERIFIED)
    source_references: List[SourceReference] = Field(default_factory=list)
