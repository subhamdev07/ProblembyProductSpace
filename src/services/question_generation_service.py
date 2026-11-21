"""
AI-Assisted Question Generation Service
Integrates with centralized NVIDIA Nemotron service to generate curriculum-aligned,
concept-tagged, and source-grounded questions.
Supports single, batch, difficulty-targeted, and mock-based generation.
"""

import json
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

from src.models.question import (
    Question,
    QuestionType,
    QuestionDifficulty,
    CognitiveLevel,
    QuestionStatus,
    QuestionProvenance,
)
from src.models.concept import ConceptVerificationStatus, SourceStatus
from src.ai.llm_service import NVIDIANemotronService
from src.storage.question_repository import QuestionRepository
from src.storage.concept_repository import ConceptRepository
from src.storage.database import CurriculumRepository
from src.services.question_validation_service import QuestionValidationService


class GeneratedQuestionCandidate(BaseModel):
    """
    Schema for structured LLM response output.
    """
    question_text: str = Field(..., description="Question stem (supports LaTeX)")
    question_type: str = Field(..., description="MCQ, SHORT_ANSWER, LONG_ANSWER, ASSERTION_REASON, NUMERICAL, CASE_BASED")
    difficulty: str = Field(default="MEDIUM", description="EASY, MEDIUM, HARD")
    cognitive_level: str = Field(default="KNOWLEDGE_UNDERSTANDING", description="CBSE cognitive level")
    marks: int = Field(default=1, description="Marks allocated")
    expected_time_seconds: int = Field(default=60, description="Estimated time in seconds")
    answer_key: Dict[str, Any] = Field(..., description="Type-specific answer key")
    explanation: str = Field(..., description="Step-by-step reasoning")
    misconception_tags: List[str] = Field(default_factory=list, description="Common misconceptions")


class QuestionGenerationService:
    """
    Orchestrates AI-assisted question generation grounded in NCERT concepts and CBSE outcomes.
    """

    def __init__(
        self,
        question_repo: QuestionRepository,
        concept_repo: ConceptRepository,
        curriculum_repo: Optional[CurriculumRepository] = None,
        llm_service: Optional[NVIDIANemotronService] = None,
        validator: Optional[QuestionValidationService] = None,
    ):
        self.question_repo = question_repo
        self.concept_repo = concept_repo
        self.curriculum_repo = curriculum_repo
        self.llm_service = llm_service
        self.validator = validator or QuestionValidationService(question_repo, concept_repo, curriculum_repo)

    def generate_question_for_concept(
        self,
        concept_id: str,
        question_type: QuestionType = QuestionType.MCQ,
        difficulty: QuestionDifficulty = QuestionDifficulty.MEDIUM,
        cognitive_level: CognitiveLevel = CognitiveLevel.APPLICATION,
        mock_response: Optional[str] = None,
        save_to_db: bool = False,
    ) -> Question:
        """
        Generates a source-grounded question targeting a specific concept node.
        Supports mock_response to guarantee hermetic testing without live API token usage.
        """
        import uuid
        concept = self.concept_repo.get_concept(concept_id)
        if not concept:
            raise ValueError(f"Concept '{concept_id}' not found in Concept Graph.")

        # Grounding context from concept and its primary provenance
        source_prov = concept.provenance_records[0] if concept.provenance_records else None
        source_context = source_prov.verbatim_text if source_prov else "NCERT Class 10 Science"
        page_num = source_prov.page_number if source_prov else 1
        section = source_prov.section_heading if source_prov else ""

        # Construct generation prompt or use mock
        if mock_response is not None:
            raw_data = json.loads(mock_response)
            candidate = GeneratedQuestionCandidate(**raw_data)
        else:
            if self.llm_service is None:
                raise RuntimeError("LLM service is not configured for dynamic question generation.")

            prompt = self._build_generation_prompt(
                concept=concept,
                question_type=question_type,
                difficulty=difficulty,
                cognitive_level=cognitive_level,
                source_context=source_context,
            )

            response = self.llm_service.generate(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                json_mode=True,
            )
            parsed = json.loads(response.content)
            if isinstance(parsed, dict) and "question" in parsed:
                parsed = parsed["question"]
            candidate = GeneratedQuestionCandidate(**parsed)

        # Build formal Question object with unique stable ID
        short_suffix = uuid.uuid4().hex[:4].upper()
        qid = f"Q-{concept.chapter_id}-{candidate.question_type[:3]}-{concept.concept_id[-3:]}-{short_suffix}"
        prov_obj = QuestionProvenance(
            source_document_id=source_prov.source_document_id if source_prov else f"NCERT_SCI_10_{concept.chapter_id}",
            source_filename=source_prov.source_filename if source_prov else f"ch_{concept.chapter_id.lower()}.pdf",
            page_number=page_num,
            section_heading=section,
            verbatim_source_context=source_context,
        )

        # Ensure Assertion-Reason options are standard CBSE options if omitted
        ak_dict = dict(candidate.answer_key)
        if candidate.question_type == QuestionType.ASSERTION_REASON.value:
            if "options" not in ak_dict or not ak_dict["options"]:
                ak_dict["options"] = {
                    "A": "Both Assertion (A) and Reason (R) are true and Reason (R) is the correct explanation of Assertion (A).",
                    "B": "Both Assertion (A) and Reason (R) are true but Reason (R) is not the correct explanation of Assertion (A).",
                    "C": "Assertion (A) is true but Reason (R) is false.",
                    "D": "Assertion (A) is false but Reason (R) is true.",
                }

        question = Question(
            question_id=qid,
            question_text=candidate.question_text,
            question_type=QuestionType(candidate.question_type),
            chapter_id=concept.chapter_id,
            topic_id=concept.topic_id,
            concept_ids=[concept.concept_id],
            learning_outcome_ids=["LO-C1.3"] if concept.chapter_id == "CH-01" else [],
            difficulty=QuestionDifficulty(candidate.difficulty),
            cognitive_level=CognitiveLevel(candidate.cognitive_level),
            marks=candidate.marks,
            expected_time_seconds=candidate.expected_time_seconds,
            answer_key=ak_dict,
            explanation=candidate.explanation,
            misconception_tags=candidate.misconception_tags,
            source_status=SourceStatus.INFERRED,
            verification_status=ConceptVerificationStatus.PENDING_VERIFICATION,
            question_status=QuestionStatus.PENDING_REVIEW,
            provenance=prov_obj,
        )

        # Validate question through the 12-point quality checker
        val_result = self.validator.validate_question(question)
        if val_result.is_valid:
            question.question_status = QuestionStatus.VALIDATED
            question.verification_status = ConceptVerificationStatus.VERIFIED
        else:
            question.question_status = QuestionStatus.PENDING_REVIEW

        if save_to_db:
            self.question_repo.upsert_question(question)

        return question

    def _build_generation_prompt(
        self,
        concept: Any,
        question_type: QuestionType,
        difficulty: QuestionDifficulty,
        cognitive_level: CognitiveLevel,
        source_context: str,
    ) -> str:
        if question_type == QuestionType.ASSERTION_REASON:
            type_instructions = """Question Type: ASSERTION_REASON
The question MUST present an Assertion (A) and a Reason (R).
The answer_key MUST contain:
- 'assertion': Statement (A)
- 'reason': Statement (R)
- 'options': {
    "A": "Both Assertion (A) and Reason (R) are true and Reason (R) is the correct explanation of Assertion (A).",
    "B": "Both Assertion (A) and Reason (R) are true but Reason (R) is not the correct explanation of Assertion (A).",
    "C": "Assertion (A) is true but Reason (R) is false.",
    "D": "Assertion (A) is false but Reason (R) is true."
  }
- 'correct_option': Exactly one of 'A', 'B', 'C', or 'D'.
- 'explanation': Broad, in-depth scientific explanation analyzing:
    1) Why Assertion is true or false according to NCERT
    2) Why Reason is true or false according to NCERT
    3) The causal relationship between Reason and Assertion."""
        else:
            type_instructions = f"""Question Type: {question_type.value}
The question MUST include:
- 'question_text': Clear, unambiguous stem with necessary scientific context or chemical equations.
- 'answer_key':
    - 'options': {{"A": "...", "B": "...", "C": "...", "D": "..."}} (4 distinct, mutually exclusive choices)
    - 'correct_option': Exactly one of 'A', 'B', 'C', or 'D'.
- 'explanation': Broad, comprehensive step-by-step scientific justification. Must explicitly explain:
    1) Why the correct option is scientifically valid based on NCERT.
    2) Why EACH distractor (incorrect option) is scientifically flawed, false, or incomplete."""

        return f"""You are a Senior CBSE Examination Question Designer and Curriculum Expert for Class 10 Science.
Design a high-quality, authentic CBSE Board assessment question grounded STRICTLY in NCERT Chapter {concept.chapter_id}.

Target Concept: {concept.name} ({concept.concept_id})
Concept Description: {concept.description}
Source Text Excerpt: "{source_context}"

Question Requirements:
- Format: {question_type.value}
- Difficulty: {difficulty.value}
- Cognitive Level: {cognitive_level.value}

{type_instructions}

Return ONLY valid JSON matching this schema:
{{
  "question_text": "...",
  "question_type": "{question_type.value}",
  "difficulty": "{difficulty.value}",
  "cognitive_level": "{cognitive_level.value}",
  "marks": 1,
  "expected_time_seconds": 60,
  "answer_key": {{
    "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}},
    "correct_option": "A"
  }},
  "explanation": "Broad, in-depth scientific justification...",
  "misconception_tags": ["..."]
}}
"""
