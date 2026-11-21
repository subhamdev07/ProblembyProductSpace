"""
Misconception Detection Engine
Evidence-based diagnostic classification: SUSPECTED -> CONFIRMED -> RESOLVED.
CBSE Class 10 Science (2026-27)
"""

import json
from typing import Optional, List, Dict, Any

from src.storage.remediation_repository import RemediationRepository
from src.storage.question_repository import QuestionRepository
from src.storage.concept_repository import ConceptRepository
from src.models.remediation import (
    MisconceptionStatus,
    StudentMisconceptionItem,
)


class MisconceptionDetectionService:
    """
    Evidence-based misconception classifier.
    Never confirms a misconception on a single incorrect MCQ attempt;
    requires corroborated evidence or explicit distractor pattern matching.
    """

    KNOWN_DISTRACTOR_PATTERNS = {
        "CPT-CH01-007": {
            "tags": ["SUBSCRIPT_MODIFICATION_INSTEAD_OF_COEFFICIENT"],
            "description": "Student altered chemical formula subscripts rather than balancing stoichiometry with stoichiometric coefficients."
        },
        "CPT-CH01-012": {
            "tags": ["CONFUSING_EXOTHERMIC_AND_ENDOTHERMIC"],
            "description": "Student confused heat release in exothermic reactions with heat absorption in endothermic decomposition."
        },
        "CPT-CH01-019": {
            "tags": ["CONFUSING_DISPLACEMENT_WITH_DOUBLE_DISPLACEMENT"],
            "description": "Student confused single displacement (reactivity series) with mutual ion exchange in double displacement."
        },
        "CPT-CH01-021": {
            "tags": ["CONFUSING_OXIDIZING_AGENT_WITH_SUBSTANCE_OXIDIZED"],
            "description": "Student identified the substance gaining oxygen as the oxidizing agent rather than the reducing agent."
        },
        "CPT-CH01-020": {
            "tags": ["PRECIPITATE_SOLUBILITY_CONFUSION"],
            "description": "Student failed to recognize that insoluble solid formation defines precipitation reactions."
        }
    }

    def __init__(
        self,
        remediation_repo: RemediationRepository,
        question_repo: QuestionRepository,
        concept_repo: ConceptRepository,
        llm_service: Optional[Any] = None
    ):
        self.remediation_repo = remediation_repo
        self.question_repo = question_repo
        self.concept_repo = concept_repo
        self.llm_service = llm_service

    def analyze_student_answer(
        self,
        student_id: str,
        question_id: str,
        submitted_answer: Any,
        is_correct: bool,
        student_reasoning: Optional[str] = None
    ) -> List[StudentMisconceptionItem]:
        """
        Analyzes an evaluated student response.
        - If correct: checks and resolves previously active misconceptions on the question's concepts.
        - If incorrect: identifies candidate misconceptions, evaluates corroborating evidence,
          and logs SUSPECTED or CONFIRMED state.
        """
        # 1. Retrieve Question details
        question = self.question_repo.get_question(question_id)
        if not question:
            return []

        # Find associated concept
        primary_concept_id = question.concept_ids[0] if question.concept_ids else None
        if not primary_concept_id:
            # Fallback to chapter level default if unmapped
            primary_concept_id = "CPT-CH01-001"

        # If answer is correct, student has demonstrated understanding!
        if is_correct:
            self.remediation_repo.resolve_misconceptions_for_concept(student_id, primary_concept_id)
            return []

        # Answer is INCORRECT: Detect applicable misconception tags
        detected_items = []
        tags_to_evaluate = []

        # Check question's own misconception tags from P2 bank
        if question.misconception_tags:
            for t in question.misconception_tags:
                if t not in tags_to_evaluate:
                    tags_to_evaluate.append(t)

        # Check known concept-level distractor patterns
        known = self.KNOWN_DISTRACTOR_PATTERNS.get(primary_concept_id)
        if known:
            for t in known["tags"]:
                if t not in tags_to_evaluate:
                    tags_to_evaluate.append(t)

        # Default fallback tag if none found
        if not tags_to_evaluate:
            tags_to_evaluate.append("CONCEPTUAL_GAP_IN_REACTION_PRINCIPLE")

        # Evidence construction
        evidence_parts = [
            f"Question {question_id} ({question.question_type.value if hasattr(question.question_type, 'value') else question.question_type})",
            f"Submitted answer: '{submitted_answer}'",
            f"Expected answer: '{question.answer_key}'"
        ]
        if student_reasoning:
            evidence_parts.append(f"Student reasoning: '{student_reasoning}'")

        evidence_text = " | ".join(evidence_parts)

        # Record each detected tag
        for tag in tags_to_evaluate:
            item = self.remediation_repo.record_misconception_evidence(
                student_id=student_id,
                concept_id=primary_concept_id,
                misconception_tag=tag,
                evidence_text=evidence_text,
                force_confirmed=False  # Strict requirement: single failure never confirms
            )
            detected_items.append(item)

        return detected_items

    def get_student_misconceptions(
        self,
        student_id: str,
        status: Optional[str] = None
    ) -> List[StudentMisconceptionItem]:
        st_enum = MisconceptionStatus(status) if status else None
        return self.remediation_repo.get_student_misconceptions(student_id, st_enum)

    def get_misconception_summary_by_cohort(self) -> List[Dict[str, Any]]:
        return self.remediation_repo.get_all_misconceptions_summary()
