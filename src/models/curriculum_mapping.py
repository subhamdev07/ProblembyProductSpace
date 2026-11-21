"""
Curriculum Mapping Model
Captures relational bindings across hierarchical layers, enabling auditing of mappings.
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from src.models.classification import VerificationStatus


class CurriculumMapping(BaseModel):
    """
    Explicit relational binding between curriculum entities (e.g. Unit -> Chapter, Chapter -> Topic).
    """
    mapping_id: str = Field(..., description="Unique mapping identifier")
    parent_type: str = Field(..., description="Type of parent: CURRICULUM, UNIT, CHAPTER, TOPIC")
    parent_id: str = Field(..., description="ID of parent entity")
    child_type: str = Field(..., description="Type of child: UNIT, CHAPTER, TOPIC, SUBTOPIC")
    child_id: str = Field(..., description="ID of child entity")
    sequence_order: int = Field(default=1, description="Relative sequence")
    verification_status: VerificationStatus = Field(default=VerificationStatus.VERIFIED)
    notes: Optional[str] = Field(None, description="Mapping rationale or notes")
    metadata: Dict[str, Any] = Field(default_factory=dict)
