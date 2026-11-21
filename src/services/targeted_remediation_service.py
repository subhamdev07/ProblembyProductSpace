"""
Targeted Remediation Engine
Bridges Concept Graph prerequisite DAG with NCERT grounding, scaffolded examples,
and targeted practice items.
"""

from typing import Optional, List, Dict, Any

from src.storage.remediation_repository import RemediationRepository
from src.storage.learner_repository import LearnerRepository
from src.storage.concept_repository import ConceptRepository
from src.storage.question_repository import QuestionRepository
from src.services.answer_evaluation_service import AnswerEvaluationService
from src.services.misconception_detection_service import MisconceptionDetectionService
from src.services.spaced_repetition_service import SpacedRepetitionService
from src.models.remediation import (
    TargetedRemediationPayload,
    CompleteRemediationResponse,
)
from src.models.assessment import AssessmentQuestionView


class TargetedRemediationService:
    """
    Orchestrates targeted scaffolding for struggling learners.
    Identifies foundational prerequisite gaps in the P1 Concept Graph,
    binds to verified NCERT textbook sections, and provides instant remediation practice.
    """

    NCERT_CHAPTER1_EXPLANATIONS = {
        "CPT-CH01-020": {
            "title": "Precipitation Reactions",
            "prereq_id": "CPT-CH01-019",
            "ncert_ref": "NCERT Class 10 Science, Chapter 1, Section 1.2.4, pp. 11-12",
            "gap_summary": "Confusion regarding why an insoluble precipitate forms during mutual ion exchange.",
            "explanation": "Any reaction that produces an insoluble substance is called a precipitation reaction. When sodium sulphate ($Na_2SO_4$) reacts with barium chloride ($BaCl_2$), the white precipitate of barium sulphate ($BaSO_4$) is formed by the reaction of $SO_4^{2-}$ and $Ba^{2+}$. The other product formed is sodium chloride ($NaCl$) which remains in the solution.",
            "example_activity": "Activity 1.10: Mix 3 mL of sodium sulphate solution with 3 mL of barium chloride solution. A white precipitate of $BaSO_4$ forms instantly according to the balanced equation: $Na_2SO_4(aq) + BaCl_2(aq) \\rightarrow BaSO_4(s) + 2NaCl(aq)$."
        },
        "CPT-CH01-019": {
            "title": "Double Displacement Reactions",
            "prereq_id": "CPT-CH01-018",
            "ncert_ref": "NCERT Class 10 Science, Chapter 1, Section 1.2.4, pp. 11-12",
            "gap_summary": "Distinguishing mutual ion exchange from single displacement reactions.",
            "explanation": "Such reactions in which there is an exchange of ions between the reactants are called double displacement reactions. Unlike single displacement where a more reactive element displaces a less reactive one, double displacement involves two compounds swapping their cationic and anionic components.",
            "example_activity": "Precipitate test: Lead(II) nitrate reacts with potassium iodide to produce yellow lead iodide precipitate: $Pb(NO_3)_2(aq) + 2KI(aq) \\rightarrow PbI_2(s) + 2KNO_3(aq)$."
        },
        "CPT-CH01-021": {
            "title": "Oxidation and Reduction (Redox)",
            "prereq_id": "CPT-CH01-007",
            "ncert_ref": "NCERT Class 10 Science, Chapter 1, Section 1.2.5, pp. 12-13",
            "gap_summary": "Identifying oxidizing agents vs reducing agents in simultaneous electron/oxygen transfer.",
            "explanation": "If a substance gains oxygen during a reaction, it is said to be oxidized. If a substance loses oxygen, it is said to be reduced. In $CuO + H_2 \\xrightarrow{\\Delta} Cu + H_2O$, copper(II) oxide is losing oxygen and is being reduced, while hydrogen is gaining oxygen and is being oxidized. One reactant gets oxidized while the other gets reduced during a redox reaction.",
            "example_activity": "Activity 1.11: Heat a china dish containing about 1 g of copper powder. The surface of copper powder becomes coated with black copper(II) oxide ($2Cu + O_2 \\rightarrow 2CuO$). If hydrogen gas is passed over this heated material, the black coating turns brown as the reverse reaction takes place."
        },
        "CPT-CH01-012": {
            "title": "Exothermic Reactions",
            "prereq_id": "CPT-CH01-011",
            "ncert_ref": "NCERT Class 10 Science, Chapter 1, Section 1.2.1, pp. 6-7",
            "gap_summary": "Differentiating heat-releasing combination reactions from energy-absorbing processes.",
            "explanation": "Reactions in which heat is released along with the formation of products are called exothermic chemical reactions. Quicklime ($CaO$) reacts vigorously with water to produce slaked lime ($Ca(OH)_2$), releasing a large amount of heat. Respiration and burning of natural gas ($CH_4 + 2O_2 \\rightarrow CO_2 + 2H_2O + \\text{Heat}$) are also exothermic processes.",
            "example_activity": "Activity 1.4: Take a small amount of calcium oxide or quicklime in a beaker. Slowly add water to this. Touch the beaker; you will feel a significant rise in temperature due to vigorous exothermic heat generation."
        },
        "CPT-CH01-007": {
            "title": "Balancing Chemical Equations",
            "prereq_id": "CPT-CH01-004",
            "ncert_ref": "NCERT Class 10 Science, Chapter 1, Section 1.1.2, pp. 3-6",
            "gap_summary": "Attempting to balance atoms by changing formula subscripts instead of stoichiometric coefficients.",
            "explanation": "According to the Law of Conservation of Mass, total mass of elements present in the products must equal total mass in reactants. To balance an equation, first draw boxes around each formula. Do not change anything inside the boxes (subscripts). Only change coefficients in front of formulas.",
            "example_activity": "Step-by-step balancing of $Fe + H_2O \\rightarrow Fe_3O_4 + H_2$. Equalize oxygen atoms first ($4H_2O$), then iron ($3Fe$), and finally hydrogen ($4H_2$), yielding $3Fe + 4H_2O \\rightarrow Fe_3O_4 + 4H_2$."
        }
    }

    def __init__(
        self,
        remediation_repo: RemediationRepository,
        learner_repo: LearnerRepository,
        concept_repo: ConceptRepository,
        question_repo: QuestionRepository,
        answer_evaluator: AnswerEvaluationService,
        misconception_service: MisconceptionDetectionService,
        spaced_repetition_service: SpacedRepetitionService
    ):
        self.remediation_repo = remediation_repo
        self.learner_repo = learner_repo
        self.concept_repo = concept_repo
        self.question_repo = question_repo
        self.answer_evaluator = answer_evaluator
        self.misconception_service = misconception_service
        self.spaced_repetition_service = spaced_repetition_service

    def get_remediation_for_student(
        self,
        student_id: str,
        concept_id: Optional[str] = None
    ) -> TargetedRemediationPayload:
        """Generates a targeted remediation package for the learner's weakest concept."""
        # 1. Determine target concept
        if not concept_id:
            weak_items = self.learner_repo.get_weakest_concepts(student_id, limit=1)
            if weak_items:
                concept_id = weak_items[0].concept_id
            else:
                # Default to Chapter 1 foundational reaction concept
                concept_id = "CPT-CH01-020"

        concept = self.concept_repo.get_concept(concept_id)
        concept_name = concept.name if concept else concept_id

        # 2. Inspect Concept Graph Prerequisites
        prereq_ids = self.concept_repo.get_direct_prerequisites(concept_id)
        prereq_id = prereq_ids[0] if prereq_ids else None
        prereq_concept = self.concept_repo.get_concept(prereq_id) if prereq_id else None
        prereq_name = prereq_concept.name if prereq_concept else None

        # 3. Retrieve NCERT content & explanations
        known_content = self.NCERT_CHAPTER1_EXPLANATIONS.get(concept_id)
        if not known_content and prereq_id:
            known_content = self.NCERT_CHAPTER1_EXPLANATIONS.get(prereq_id)

        if known_content:
            ncert_ref = known_content["ncert_ref"]
            gap_summary = known_content["gap_summary"]
            explanation = known_content["explanation"]
            example_activity = known_content["example_activity"]
        else:
            ncert_ref = f"NCERT Class 10 Science, Chapter 1 (Chemical Reactions and Equations)"
            gap_summary = f"Foundational gap identified in {concept_name}."
            explanation = concept.description if concept else "Review key chemical reaction principles and balanced equations."
            example_activity = "Review NCERT Chapter 1 textbook activities and balanced chemical equations."

        # 4. Select a targeted practice question
        candidate_qs = self.question_repo.get_questions_by_concept(concept_id)
        if not candidate_qs and prereq_id:
            candidate_qs = self.question_repo.get_questions_by_concept(prereq_id)

        practice_q_view = None
        chosen_q_id = None
        if candidate_qs:
            q = candidate_qs[0]
            chosen_q_id = q.question_id
            practice_q_view = AssessmentQuestionView.from_question(q).model_dump()

        # 5. Get current learner mastery
        mastery_item = self.learner_repo.get_concept_mastery(student_id, concept_id)
        current_mastery = mastery_item.mastery_score if mastery_item else 0.25

        # 6. Log remediation event
        rem_id = self.remediation_repo.log_remediation_event(
            student_id=student_id,
            concept_id=concept_id,
            prereq_id=prereq_id,
            gap_summary=gap_summary,
            ncert_ref=ncert_ref,
            explanation=explanation,
            example=example_activity,
            question_id=chosen_q_id,
            mastery_before=current_mastery
        )

        return TargetedRemediationPayload(
            remediation_id=rem_id,
            student_id=student_id,
            concept_id=concept_id,
            concept_name=concept_name,
            prerequisite_concept_id=prereq_id,
            prerequisite_concept_name=prereq_name,
            gap_summary=gap_summary,
            ncert_reference=ncert_ref,
            explanation=explanation,
            example_activity=example_activity,
            practice_question=practice_q_view,
            current_mastery=current_mastery
        )

    def complete_remediation_practice(
        self,
        remediation_id: str,
        student_id: str,
        question_id: str,
        student_answer: Any
    ) -> CompleteRemediationResponse:
        """Evaluates student's remediation practice attempt, updates mastery, and schedules revision."""
        question = self.question_repo.get_question(question_id)
        if not question:
            raise ValueError(f"Practice question '{question_id}' not found.")

        # Determine concept
        concept_id = question.concept_ids[0] if question.concept_ids else "CPT-CH01-020"

        # 1. Evaluate answer
        eval_result = self.answer_evaluator.evaluate_answer(question, student_answer)

        # 2. Update Learner Model mastery
        mastery_before_item = self.learner_repo.get_concept_mastery(student_id, concept_id)
        mastery_before = mastery_before_item.mastery_score if mastery_before_item else 0.25

        diff_str = str(question.difficulty.value if hasattr(question.difficulty, "value") else question.difficulty).upper()
        diff_multiplier = 1.2 if "HARD" in diff_str else (0.8 if "EASY" in diff_str else 1.0)

        mastery_after_item = self.learner_repo.update_mastery(
            student_id=student_id,
            concept_id=concept_id,
            is_correct=eval_result.is_correct,
            difficulty_multiplier=diff_multiplier
        )
        mastery_after = mastery_after_item.mastery_score
        delta = round(mastery_after - mastery_before, 3)

        # 3. Analyze misconceptions
        self.misconception_service.analyze_student_answer(
            student_id=student_id,
            question_id=question_id,
            submitted_answer=student_answer,
            is_correct=eval_result.is_correct
        )

        # 4. Schedule next spaced repetition
        next_interval = 3 if eval_result.is_correct else 1
        sched_item = self.spaced_repetition_service.schedule_concept_review(
            student_id=student_id,
            concept_id=concept_id,
            initial_interval_days=next_interval,
            initial_mastery=mastery_after
        )

        # 5. Complete remediation log record
        self.remediation_repo.complete_remediation_event(
            remediation_id=remediation_id,
            student_answer=str(student_answer),
            mastery_after=mastery_after
        )

        return CompleteRemediationResponse(
            remediation_id=remediation_id,
            concept_id=concept_id,
            is_correct=eval_result.is_correct,
            marks_awarded=eval_result.marks_awarded,
            feedback=eval_result.feedback,
            mastery_before=mastery_before,
            mastery_after=mastery_after,
            mastery_delta=delta,
            next_revision_date=sched_item.next_review_at
        )
