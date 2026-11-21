"""
Academic Session, Subject, and Curriculum Models
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field


class AcademicSession(BaseModel):
    """
    Academic session container supporting forward/backward syllabus versions.
    """
    session_id: str = Field(..., description="Unique session identifier, e.g. '2026-27'")
    name: str = Field(..., description="Full session title, e.g. 'Academic Session 2026–27'")
    start_year: int = Field(..., description="Starting calendar year")
    end_year: int = Field(..., description="Ending calendar year")
    is_active: bool = Field(default=True, description="Whether this session is current")


class Subject(BaseModel):
    """
    Subject domain specification.
    """
    subject_id: str = Field(..., description="Unique subject ID, e.g. 'SCI-10'")
    code: str = Field(..., description="Official Board subject code, e.g. '086'")
    name: str = Field(..., description="Subject name, e.g. 'Science'")
    class_level: int = Field(default=10, description="Grade/Class level, e.g. 10")
    description: Optional[str] = Field(None, description="Overview of the subject scope")


class Curriculum(BaseModel):
    """
    Curriculum specification container binding session, subject, and governing authority.
    """
    curriculum_id: str = Field(..., description="Unique curriculum identifier, e.g. 'CBSE-SCI-10-2026-27'")
    name: str = Field(..., description="Name, e.g. 'CBSE Class 10 Science (086) 2026-27'")
    session_id: str = Field(..., description="Reference to AcademicSession.session_id")
    subject_id: str = Field(..., description="Reference to Subject.subject_id")
    class_level: int = Field(default=10, description="Grade level")
    authority: str = Field(default="CBSE", description="Governing board or educational authority")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata such as total theory marks, internal marks")
