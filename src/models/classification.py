"""
Assessment Classification and Verification Status Enums
"""

from enum import Enum


class AssessmentClassification(str, Enum):
    """
    Classification of curriculum elements for assessment purposes.
    - SUMMATIVE: Included in board year-end summative examination (80 marks).
    - FORMATIVE: Included in syllabus for internal/formative assessment, portfolio, experiential learning only.
    - NOT_IN_CURRENT_SCOPE: Explicitly excluded from examination (e.g. colour of sun at sunrise/sunset, textbook boxes).
    - PENDING_VERIFICATION: Awaiting official curriculum document verification.
    """
    SUMMATIVE = "SUMMATIVE"
    FORMATIVE = "FORMATIVE"
    NOT_IN_CURRENT_SCOPE = "NOT_IN_CURRENT_SCOPE"
    PENDING_VERIFICATION = "PENDING_VERIFICATION"


class VerificationStatus(str, Enum):
    """
    Traceability and verification status against primary curriculum sources.
    - VERIFIED: Directly evidenced in primary official documents.
    - PENDING_VERIFICATION: Extracted but needs further primary source confirmation.
    - UNVERIFIED: Uncorroborated or placeholder entry requiring audit.
    """
    VERIFIED = "VERIFIED"
    PENDING_VERIFICATION = "PENDING_VERIFICATION"
    UNVERIFIED = "UNVERIFIED"


class ProvenanceType(str, Enum):
    """
    Provenance of learning outcomes and competencies.
    - OFFICIAL: Explicitly stated in the official CBSE/NCF curriculum.
    - INFERRED: Derived or synthesized from official syllabus topic statements.
    - PENDING: Requires official verification against standard curriculum frameworks.
    """
    OFFICIAL = "OFFICIAL"
    INFERRED = "INFERRED"
    PENDING = "PENDING"
