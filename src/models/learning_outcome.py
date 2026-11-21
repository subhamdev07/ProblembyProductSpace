"""
Learning Outcome Registry Models
Supports Curricular Goals (CGs), Competencies (Cs), and Granular Learning Outcomes (LOs).
Strictly separates OFFICIAL primary curriculum statements from INFERRED outcomes.
"""

from typing import Optional, List
from pydantic import BaseModel, Field
from src.models.classification import VerificationStatus, ProvenanceType
from src.models.source import SourceReference


class LearningOutcome(BaseModel):
    """
    Granular milestone or competency statement describing what students should know,
    understand, and be able to do.
    """
    outcome_id: str = Field(..., description="Unique outcome ID, e.g. 'LO-C1.3' or 'LO-CH01-01'")
    code: Optional[str] = Field(None, description="Official competency code, e.g. 'C 1.3' or 'CG 1'")
    related_chapter_id: str = Field(..., description="Primary Chapter ID associated with this outcome")
    related_topic_id: Optional[str] = Field(None, description="Topic ID if mapped at topic level")
    description: str = Field(..., description="Exact statement of expected capability or understanding")
    curricular_goal: Optional[str] = Field(None, description="Associated Curricular Goal, e.g. 'CG 1'")
    competency: Optional[str] = Field(None, description="Associated Competency statement")
    suggestive_verbs: List[str] = Field(default_factory=list, description="Taxonomy verbs, e.g. state, calculate, explain")
    provenance_type: ProvenanceType = Field(default=ProvenanceType.OFFICIAL)
    verification_status: VerificationStatus = Field(default=VerificationStatus.VERIFIED)
    source_reference: Optional[SourceReference] = None
