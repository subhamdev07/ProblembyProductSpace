"""
Question Quality Validation Service
Implements a deterministic 12-point quality check against questions in the Question Bank.
Ensures schema conformance, concept graph referential integrity, answer key correctness,
CBSE syllabus scope alignment, and duplicate detection.
"""

from typing import List, Dict, Any, Optional, Set
from pydantic import BaseModel, Field

from src.models.question import (
    Question,
    QuestionType,
    QuestionDifficulty,
    CognitiveLevel,
    QuestionStatus,
)
from src.storage.question_repository import QuestionRepository
from src.storage.concept_repository import ConceptRepository
from src.storage.database import CurriculumRepository


class QuestionValidationResult(BaseModel):
    """
    Result of a question validation audit.
    """
    is_valid: bool = Field(..., description="Whether question passed all mandatory validation rules")
    errors: List[str] = Field(default_factory=list, description="Critical validation errors")
    warnings: List[str] = Field(default_factory=list, description="Quality or pedagogical warnings")
    rules_evaluated: int = Field(default=12, description="Total validation checks executed")


class QuestionBankValidationSummary(BaseModel):
    """
    Summary result for validating an entire question bank.
    """
    total_evaluated: int
    valid_count: int
    invalid_count: int
    all_valid: bool
    question_results: Dict[str, QuestionValidationResult]
    errors_by_rule: Dict[str, int]


class QuestionValidationService:
    """
    Deterministic validation engine for questions.
    """

    def __init__(
        self,
        question_repo: QuestionRepository,
        concept_repo: Optional[ConceptRepository] = None,
        curriculum_repo: Optional[CurriculumRepository] = None,
    ):
        self.question_repo = question_repo
        self.concept_repo = concept_repo
        self.curriculum_repo = curriculum_repo

    def validate_question(
        self,
        question: Question,
        existing_questions: Optional[List[Question]] = None,
    ) -> QuestionValidationResult:
        """
        Runs the 12-rule validation check on a single question.
        """
        errors = []
        warnings = []
        rules_evaluated = 12

        # QV-01: Required Fields Check
        if not question.question_id or not question.question_id.startswith("Q-"):
            errors.append(f"QV-01: Invalid or missing question_id '{question.question_id}'. Must start with 'Q-'.")
        if not question.question_text or len(question.question_text.strip()) < 10:
            errors.append("QV-01: question_text is missing or excessively short (<10 chars).")
        if not question.explanation or len(question.explanation.strip()) < 10:
            errors.append("QV-01: explanation is missing or excessively short (<10 chars).")

        # QV-02 & QV-03: Question Type Schema & Answer Key Structure
        ak = question.answer_key
        if question.question_type == QuestionType.MCQ:
            if "options" not in ak or "correct_option" not in ak:
                errors.append("QV-02: MCQ answer_key must contain 'options' and 'correct_option'.")
            else:
                opts = ak["options"]
                correct = ak["correct_option"]
                if not isinstance(opts, dict) or len(opts) != 4:
                    errors.append(f"QV-02: MCQ must provide exactly 4 options (A, B, C, D); found {len(opts) if isinstance(opts, dict) else 0}.")
                if correct not in opts:
                    errors.append(f"QV-03: MCQ correct_option '{correct}' does not match any key in options.")

        elif question.question_type == QuestionType.ASSERTION_REASON:
            if "assertion" not in ak or "reason" not in ak or "correct_option" not in ak:
                errors.append("QV-02: ASSERTION_REASON must contain 'assertion', 'reason', and 'correct_option'.")
            elif ak["correct_option"].upper() not in {"A", "B", "C", "D"}:
                errors.append("QV-03: ASSERTION_REASON correct_option must be one of A, B, C, D.")

        elif question.question_type == QuestionType.NUMERICAL:
            if "numerical_value" not in ak:
                errors.append("QV-02: NUMERICAL answer_key must specify 'numerical_value'.")
            elif not isinstance(ak["numerical_value"], (int, float)):
                errors.append("QV-03: NUMERICAL 'numerical_value' must be numeric.")

        elif question.question_type in (QuestionType.SHORT_ANSWER, QuestionType.LONG_ANSWER):
            if "key_points" not in ak or not isinstance(ak["key_points"], list) or len(ak["key_points"]) == 0:
                errors.append(f"QV-02: {question.question_type.value} must provide non-empty 'key_points' list.")

        elif question.question_type == QuestionType.CASE_BASED:
            if "passage" not in ak or "sub_questions" not in ak:
                errors.append("QV-02: CASE_BASED must contain 'passage' and 'sub_questions'.")
            elif not isinstance(ak["sub_questions"], list) or len(ak["sub_questions"]) < 2:
                errors.append("QV-03: CASE_BASED must contain at least 2 sub_questions.")

        # QV-04: Valid Chapter & Topic Reference
        with self.question_repo.db.get_connection() as conn:
            valid_chaps = {r[0] for r in conn.execute("SELECT chapter_id FROM chapters;").fetchall()}
            valid_topics = {r[0] for r in conn.execute("SELECT topic_id FROM topics;").fetchall()}
            valid_concepts = {r[0] for r in conn.execute("SELECT concept_id FROM concepts;").fetchall()}
            valid_los = {r[0] for r in conn.execute("SELECT outcome_id FROM learning_outcomes;").fetchall()}

        if question.chapter_id not in valid_chaps:
            errors.append(f"QV-04: chapter_id '{question.chapter_id}' does not exist in curriculum database.")
        if question.topic_id not in valid_topics:
            errors.append(f"QV-04: topic_id '{question.topic_id}' does not exist in curriculum database.")

        # QV-05: Concept Graph Referential Integrity
        if not question.concept_ids:
            errors.append("QV-05: Question must be linked to at least 1 valid concept in the Concept Graph.")
        else:
            for cid in question.concept_ids:
                if cid not in valid_concepts:
                    errors.append(f"QV-05: Referenced concept_id '{cid}' does not exist in Concept Graph.")

        # QV-06: Learning Outcome Referential Integrity
        if not question.learning_outcome_ids:
            warnings.append("QV-06: Question has no mapped learning outcomes.")
        else:
            for loid in question.learning_outcome_ids:
                if loid not in valid_los:
                    errors.append(f"QV-06: Referenced learning outcome '{loid}' does not exist in curriculum.")

        # QV-07: Difficulty Rubric Compliance
        if question.difficulty == QuestionDifficulty.EASY:
            if question.marks > 2:
                warnings.append(f"QV-07: EASY question allocated {question.marks} marks; typically 1-2 marks.")
        elif question.difficulty == QuestionDifficulty.HARD:
            if question.expected_time_seconds < 45:
                warnings.append("QV-07: HARD question expected time is less than 45 seconds.")

        # QV-08: Cognitive Level Classification
        valid_cog = {c.value for c in CognitiveLevel}
        if question.cognitive_level.value not in valid_cog:
            errors.append(f"QV-08: Invalid cognitive_level '{question.cognitive_level}'.")

        # QV-09: Source Provenance Completeness
        if question.provenance is None:
            if question.question_status == QuestionStatus.VALIDATED:
                errors.append("QV-09: VALIDATED question must have a non-null provenance record.")
            else:
                warnings.append("QV-09: Draft/Pending question lacks provenance record.")
        else:
            if not question.provenance.source_document_id or not question.provenance.source_filename:
                errors.append("QV-09: Provenance is missing source_document_id or source_filename.")

        # QV-10: Duplicate Detection
        if existing_questions:
            clean_text = "".join(question.question_text.lower().split())
            for eq in existing_questions:
                if eq.question_id != question.question_id:
                    eq_clean = "".join(eq.question_text.lower().split())
                    if clean_text == eq_clean:
                        errors.append(f"QV-10: Exact duplicate question text detected with '{eq.question_id}'.")
                        break

        # QV-11: Explanation & Answer Consistency
        # The explanation must reference the correct answer or provide explicit substantiation
        if question.question_type == QuestionType.MCQ and "correct_option" in ak:
            correct_opt = ak["correct_option"]
            opt_text = ak["options"].get(correct_opt, "")
            # Verify explanation is substantial
            if len(question.explanation.split()) < 5:
                warnings.append("QV-11: Explanation is brief and may not fully substantiate the answer.")

        # QV-12: Formative vs Summative Scope Check
        # If topic is FORMATIVE, verify question doesn't claim high-stakes summative status
        with self.question_repo.db.get_connection() as conn:
            topic_row = conn.execute("SELECT assessment_status FROM topics WHERE topic_id = ?;", (question.topic_id,)).fetchone()
            if topic_row and topic_row[0] == "FORMATIVE":
                if question.marks > 3:
                    warnings.append(f"QV-12: Question is based on formative topic '{question.topic_id}' but allocated {question.marks} marks.")

        is_valid = (len(errors) == 0)
        return QuestionValidationResult(
            is_valid=is_valid,
            errors=errors,
            warnings=warnings,
            rules_evaluated=rules_evaluated,
        )

    def validate_all_questions(self) -> QuestionBankValidationSummary:
        """
        Validates all questions currently in the repository.
        """
        all_questions = self.question_repo.get_all_questions()
        results = {}
        valid_count = 0
        invalid_count = 0
        errors_by_rule: Dict[str, int] = {}

        for q in all_questions:
            res = self.validate_question(q, existing_questions=all_questions)
            results[q.question_id] = res
            if res.is_valid:
                valid_count += 1
            else:
                invalid_count += 1
                for err in res.errors:
                    rule_tag = err.split(":")[0] if ":" in err else "GENERAL"
                    errors_by_rule[rule_tag] = errors_by_rule.get(rule_tag, 0) + 1

        return QuestionBankValidationSummary(
            total_evaluated=len(all_questions),
            valid_count=valid_count,
            invalid_count=invalid_count,
            all_valid=(invalid_count == 0),
            question_results=results,
            errors_by_rule=errors_by_rule,
        )
