"""
Examination Service (P5)
Complete CBSE Board Examination Simulation Engine for BodhAI (CBSE Class 10 Science - 086).
Orchestrates:
1. Standardized CBSE 2026-27 Blueprint management (80 marks, 180 mins, 39 questions across 5 sections).
2. Authoritative timed sessions with real-time answer persistence and server-side countdown.
3. Multi-typology evaluation (MCQ, Assertion-Reason, Numerical, Short Answer, Long Answer, Case-Based).
4. Direct integration with Learner Model (mastery updates), Misconception Detection, and Spaced Repetition.
5. Student and Teacher Dashboard analytics and performance reports.
"""

import json
import uuid
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional

from src.storage.database import Database
from src.storage.examination_repository import ExaminationRepository
from src.storage.question_repository import QuestionRepository
from src.storage.concept_repository import ConceptRepository
from src.storage.learner_repository import LearnerRepository

from src.models.examination import (
    ExaminationStatus,
    ExamSectionConfig,
    ExaminationBlueprint,
    ExaminationQuestionItem,
    ExaminationSessionState,
    SaveExamAnswerRequest,
    SaveExamAnswerResponse,
    ExamQuestionReviewItem,
    ExaminationResultSummary,
    ExaminationOverviewItem,
)
from src.models.question import Question, QuestionType, QuestionDifficulty, CognitiveLevel
from src.services.answer_evaluation_service import AnswerEvaluationService
from src.services.learner_model_service import LearnerModelService
from src.services.misconception_detection_service import MisconceptionDetectionService
from src.services.spaced_repetition_service import SpacedRepetitionService
from src.services.targeted_remediation_service import TargetedRemediationService


class ExaminationService:
    def __init__(
        self,
        db: Database,
        exam_repo: ExaminationRepository,
        question_repo: QuestionRepository,
        concept_repo: ConceptRepository,
        evaluation_service: AnswerEvaluationService,
        learner_service: LearnerModelService,
        misconception_service: MisconceptionDetectionService,
        spaced_repetition_service: SpacedRepetitionService,
        targeted_remediation_service: Optional[TargetedRemediationService] = None,
        learner_repo: Optional[LearnerRepository] = None,
    ):
        self.db = db
        self.exam_repo = exam_repo
        self.question_repo = question_repo
        self.concept_repo = concept_repo
        self.evaluation_service = evaluation_service
        self.learner_service = learner_service
        self.misconception_service = misconception_service
        self.spaced_repetition_service = spaced_repetition_service
        self.targeted_remediation_service = targeted_remediation_service
        self.learner_repo = learner_repo or LearnerRepository(db)

        # Seed default official and mock blueprints on initialization
        self.seed_default_blueprints()

    # --------------------------------------------------------------------------
    # 1. Blueprint Seeding & Retrieval
    # --------------------------------------------------------------------------
    def seed_default_blueprints(self) -> None:
        """Seeds the standard official CBSE 2026-27 Blueprint and practice papers."""
        official_blueprint = ExaminationBlueprint(
            blueprint_id="BP-CBSE-X-SCI-2027",
            title="CBSE Class 10 Science (086) Annual Board Examination Simulation 2026–27",
            academic_session="2026-27",
            curriculum_id="CBSE-SCI-10-2026-27",
            total_marks=80,
            duration_minutes=180,
            question_count=39,
            sections=[
                ExamSectionConfig(
                    section_name="Section A",
                    section_title="Multiple Choice & Assertion-Reasoning",
                    question_types=[QuestionType.MCQ, QuestionType.ASSERTION_REASON],
                    question_count=20,
                    marks_per_question=1,
                    total_section_marks=20,
                    instructions="Questions 1 to 20 are objective questions carrying 1 mark each (16 Multiple Choice Questions and 4 Assertion-Reasoning questions).",
                    internal_choice_count=0,
                ),
                ExamSectionConfig(
                    section_name="Section B",
                    section_title="Very Short Answer (VSA)",
                    question_types=[QuestionType.SHORT_ANSWER, QuestionType.NUMERICAL],
                    question_count=6,
                    marks_per_question=2,
                    total_section_marks=12,
                    instructions="Questions 21 to 26 are very short answer questions carrying 2 marks each. Answers should be concise, typically 30 to 50 words.",
                    internal_choice_count=1,
                ),
                ExamSectionConfig(
                    section_name="Section C",
                    section_title="Short Answer (SA)",
                    question_types=[QuestionType.SHORT_ANSWER, QuestionType.NUMERICAL, QuestionType.DIAGRAM_BASED],
                    question_count=7,
                    marks_per_question=3,
                    total_section_marks=21,
                    instructions="Questions 27 to 33 are short answer questions carrying 3 marks each. Answers should be in the range of 50 to 80 words.",
                    internal_choice_count=1,
                ),
                ExamSectionConfig(
                    section_name="Section D",
                    section_title="Long Answer (LA)",
                    question_types=[QuestionType.LONG_ANSWER],
                    question_count=3,
                    marks_per_question=5,
                    total_section_marks=15,
                    instructions="Questions 34 to 36 are long answer questions carrying 5 marks each. Answers should be thorough and structured (80 to 120 words).",
                    internal_choice_count=1,
                ),
                ExamSectionConfig(
                    section_name="Section E",
                    section_title="Case-Based / Integrated Assessment",
                    question_types=[QuestionType.CASE_BASED],
                    question_count=3,
                    marks_per_question=4,
                    total_section_marks=12,
                    instructions="Questions 37 to 39 are source-based / case-based assessments carrying 4 marks each with sub-parts.",
                    internal_choice_count=1,
                ),
            ],
            unit_weightage={
                "Unit I: Chemical Substances – Nature and Behaviour": 25,
                "Unit II: World of Living": 25,
                "Unit III: Natural Phenomena": 12,
                "Unit IV: Effects of Current": 13,
                "Unit V: Natural Resources": 5,
            },
            cognitive_distribution={
                "REMEMBERING_UNDERSTANDING": 0.46,
                "APPLICATION": 0.22,
                "ANALYZING_EVALUATING_CREATING": 0.32,
            },
            general_instructions=[
                "This question paper consists of 39 questions in 5 sections.",
                "All questions are compulsory. However, an internal choice is provided in some questions.",
                "Section A consists of 20 objective questions (16 MCQs and 4 Assertion-Reasoning) carrying 1 mark each.",
                "Section B consists of 6 Very Short Answer questions carrying 2 marks each.",
                "Section C consists of 7 Short Answer questions carrying 3 marks each.",
                "Section D consists of 3 Long Answer questions carrying 5 marks each.",
                "Section E consists of 3 source-based/case-based units of assessment carrying 4 marks each.",
                "All programming or calculated values must follow standard SI units where applicable.",
                "Use of calculators or unauthorized reference materials is strictly prohibited.",
            ],
            is_official=True,
        )
        self.exam_repo.upsert_blueprint(official_blueprint)

        # Unit I Diagnostic Mock Blueprint (45 mins, 25 marks)
        unit1_blueprint = ExaminationBlueprint(
            blueprint_id="BP-CBSE-X-UNIT1-MOCK",
            title="Unit I: Chemical Substances Diagnostic Mock Test",
            academic_session="2026-27",
            curriculum_id="CBSE-SCI-10-2026-27",
            total_marks=25,
            duration_minutes=45,
            question_count=12,
            sections=[
                ExamSectionConfig(
                    section_name="Section A",
                    section_title="Objective MCQs & Assertion-Reason",
                    question_types=[QuestionType.MCQ, QuestionType.ASSERTION_REASON],
                    question_count=8,
                    marks_per_question=1,
                    total_section_marks=8,
                    instructions="Questions 1 to 8 are objective questions of 1 mark each.",
                    internal_choice_count=0,
                ),
                ExamSectionConfig(
                    section_name="Section B",
                    section_title="Short Answer & Equations",
                    question_types=[QuestionType.SHORT_ANSWER, QuestionType.NUMERICAL],
                    question_count=3,
                    marks_per_question=3,
                    total_section_marks=9,
                    instructions="Questions 9 to 11 are short answer questions carrying 3 marks each.",
                    internal_choice_count=0,
                ),
                ExamSectionConfig(
                    section_name="Section C",
                    section_title="Case-Based Chemical Analysis",
                    question_types=[QuestionType.CASE_BASED],
                    question_count=2,
                    marks_per_question=4,
                    total_section_marks=8,
                    instructions="Questions 12 & 13 are case-based questions carrying 4 marks each.",
                    internal_choice_count=0,
                ),
            ],
            unit_weightage={"Unit I: Chemical Substances – Nature and Behaviour": 25},
            cognitive_distribution={"REMEMBERING_UNDERSTANDING": 0.50, "APPLICATION": 0.30, "ANALYZING_EVALUATING_CREATING": 0.20},
            general_instructions=[
                "This diagnostic mock test focuses exclusively on Unit I: Chemical Substances.",
                "Duration is 45 minutes with total 25 marks.",
                "Answer all questions methodically with chemical formulas and balanced equations.",
            ],
            is_official=False,
        )
        self.exam_repo.upsert_blueprint(unit1_blueprint)

    def get_available_blueprints(self) -> List[ExaminationBlueprint]:
        return self.exam_repo.get_all_blueprints()

    def get_blueprint_details(self, blueprint_id: str) -> Optional[ExaminationBlueprint]:
        return self.exam_repo.get_blueprint(blueprint_id)

    # --------------------------------------------------------------------------
    # 2. Template Generation & Assembly
    # --------------------------------------------------------------------------
    def generate_or_get_template(self, blueprint_id: str = "BP-CBSE-X-SCI-2027") -> str:
        """
        Generates or retrieves a pre-compiled exam question sequence matching the blueprint.
        Maps exactly 39 questions for official CBSE exam across Sections A to E.
        """
        template_id = f"TMPL-{blueprint_id}-SET1"
        existing = self.exam_repo.get_template(template_id)
        if existing:
            return template_id

        bp = self.exam_repo.get_blueprint(blueprint_id)
        if not bp:
            self.seed_default_blueprints()
            bp = self.exam_repo.get_blueprint(blueprint_id)

        # Retrieve questions from repository
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            # Fetch candidate pools
            cur.execute("SELECT question_id, question_type, marks FROM questions ORDER BY question_id;")
            all_q = cur.fetchall()

        q_by_type = {}
        for r in all_q:
            t = r["question_type"]
            m = r["marks"]
            key = f"{t}_{m}"
            if key not in q_by_type:
                q_by_type[key] = []
            q_by_type[key].append(r["question_id"])

        selected_qids = []

        if blueprint_id == "BP-CBSE-X-SCI-2027":
            # Section A: 16 MCQs (1m) + 4 Assertion-Reason (1m) = 20 Qs
            mcqs = q_by_type.get("MCQ_1", [])
            ars = q_by_type.get("ASSERTION_REASON_1", [])
            selected_qids.extend(mcqs[:16])
            selected_qids.extend(ars[:4])

            # Section B: 6 SA-I (2m)
            sa1 = q_by_type.get("SHORT_ANSWER_2", []) + q_by_type.get("NUMERICAL_2", [])
            selected_qids.extend(sa1[:6])

            # Section C: 7 SA-II (3m)
            sa2 = q_by_type.get("SHORT_ANSWER_3", []) + q_by_type.get("NUMERICAL_3", []) + q_by_type.get("DIAGRAM_BASED_3", [])
            selected_qids.extend(sa2[:7])

            # Section D: 3 LA (5m)
            la = q_by_type.get("LONG_ANSWER_5", [])
            selected_qids.extend(la[:3])

            # Section E: 3 Case-Based (4m)
            cb = q_by_type.get("CASE_BASED_4", [])
            selected_qids.extend(cb[:3])
        else:
            # Fallback for Unit 1 or smaller mocks: assemble sequentially from available
            for s in bp.sections:
                count_needed = s.question_count
                for qtype in s.question_types:
                    key = f"{qtype.value}_{s.marks_per_question}"
                    candidates = [qid for qid in q_by_type.get(key, []) if qid not in selected_qids]
                    take = candidates[:count_needed]
                    selected_qids.extend(take)
                    count_needed -= len(take)
                    if count_needed <= 0:
                        break

        self.exam_repo.upsert_template(
            template_id=template_id,
            blueprint_id=blueprint_id,
            paper_code=f"086/2027/SET-1",
            title=bp.title,
            question_ids=selected_qids,
            total_marks=bp.total_marks,
        )
        return template_id

    # --------------------------------------------------------------------------
    # 3. Live Examination Lifecycle (Start, Recover, Save, Submit)
    # --------------------------------------------------------------------------
    def start_examination(
        self,
        student_id: str = "STU-001",
        blueprint_id: str = "BP-CBSE-X-SCI-2027",
    ) -> ExaminationSessionState:
        """
        Starts or resumes a full CBSE Board Examination Simulation session.
        Enforces server-authoritative countdown timer and initial state.
        """
        # Ensure student exists
        self.learner_repo.get_or_create_student(student_id=student_id)

        # Check for active in-progress session
        active_sess = self.exam_repo.get_active_session_for_student(student_id)
        if active_sess and active_sess["blueprint_id"] == blueprint_id:
            state = self.get_session_state(active_sess["session_id"], student_id)
            if state.status == ExaminationStatus.IN_PROGRESS:
                return state

        bp = self.exam_repo.get_blueprint(blueprint_id)
        if not bp:
            self.seed_default_blueprints()
            bp = self.exam_repo.get_blueprint(blueprint_id)

        template_id = self.generate_or_get_template(blueprint_id)
        tmpl = self.exam_repo.get_template(template_id)
        question_ids = json.loads(tmpl["questions_sequence_json"]) if tmpl else []

        session_id = f"EXAM-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

        self.exam_repo.create_session(
            session_id=session_id,
            student_id=student_id,
            blueprint_id=blueprint_id,
            template_id=template_id,
            paper_title=bp.title,
            duration_minutes=bp.duration_minutes,
            total_marks=bp.total_marks,
            total_questions=len(question_ids),
        )

        # Initialize answer tracking rows for all questions
        for idx, qid in enumerate(question_ids, start=1):
            sec_name = self._determine_section_name(idx, bp)
            self.exam_repo.save_or_update_answer(
                session_id=session_id,
                student_id=student_id,
                question_id=qid,
                question_number=idx,
                section_name=sec_name,
                submitted_answer={},
                is_marked_for_review=False,
                time_spent_seconds=0,
            )

        return self.get_session_state(session_id, student_id)

    def get_session_state(self, session_id: str, student_id: str) -> ExaminationSessionState:
        """
        Retrieves the authoritative live state of an examination session.
        Computes remaining seconds from server clock and handles auto-submission on timeout.
        """
        sess = self.exam_repo.get_session(session_id)
        if not sess:
            raise ValueError(f"Examination session {session_id} not found.")

        bp = self.exam_repo.get_blueprint(sess["blueprint_id"])
        tmpl = self.exam_repo.get_template(sess["template_id"]) if sess["template_id"] else None
        qids = json.loads(tmpl["questions_sequence_json"]) if tmpl and tmpl["questions_sequence_json"] else []

        now_dt = datetime.now(timezone.utc)
        expires_at_dt = datetime.fromisoformat(sess["expires_at"].replace("Z", "+00:00"))
        remaining_secs = int((expires_at_dt - now_dt).total_seconds())

        current_status = ExaminationStatus(sess["status"])

        # Check for timeout auto-submit
        if remaining_secs <= 0 and current_status == ExaminationStatus.IN_PROGRESS:
            self.submit_examination(session_id=session_id, student_id=student_id, is_timeout=True)
            sess = self.exam_repo.get_session(session_id)
            current_status = ExaminationStatus(sess["status"])
            remaining_secs = 0

        # Retrieve saved answers
        answers_raw = self.exam_repo.get_session_answers(session_id)
        saved_dict = {}
        marked_list = []
        for a in answers_raw:
            qid = a["question_id"]
            if a["is_answered"] and a["submitted_answer"]:
                saved_dict[qid] = a["submitted_answer"]
            if a["is_marked_for_review"]:
                marked_list.append(qid)

        # Assemble student-facing question items (NO ANSWER KEYS OR EXPLANATIONS LEAKED)
        q_items: List[ExaminationQuestionItem] = []
        for idx, qid in enumerate(qids, start=1):
            q = self.question_repo.get_question(qid)
            if not q:
                continue
            sec_name = self._determine_section_name(idx, bp)
            
            # Safe options extraction
            opts = None
            if isinstance(q.answer_key, dict) and "options" in q.answer_key:
                opts = q.answer_key["options"]

            if q.question_type == QuestionType.ASSERTION_REASON and not opts:
                opts = {
                    "A": "Both Assertion (A) and Reason (R) are true and Reason (R) is the correct explanation of Assertion (A).",
                    "B": "Both Assertion (A) and Reason (R) are true but Reason (R) is not the correct explanation of Assertion (A).",
                    "C": "Assertion (A) is true but Reason (R) is false.",
                    "D": "Assertion (A) is false but Reason (R) is true.",
                }

            # Safe passage extraction for Case-Based
            passage = None
            if q.question_type == QuestionType.CASE_BASED and isinstance(q.answer_key, dict):
                passage = q.answer_key.get("passage")

            assertion = q.answer_key.get("assertion") if isinstance(q.answer_key, dict) else None
            reason = q.answer_key.get("reason") if isinstance(q.answer_key, dict) else None
            if q.question_type == QuestionType.ASSERTION_REASON:
                if not assertion and "Assertion" in q.question_text:
                    import re
                    a_m = re.search(r"Assertion\s*\(?A?\)?\s*:\s*(.*?)(?=Reason|\n|$)", q.question_text, re.IGNORECASE | re.DOTALL)
                    r_m = re.search(r"Reason\s*\(?R?\)?\s*:\s*(.*?)(?=$)", q.question_text, re.IGNORECASE | re.DOTALL)
                    if a_m:
                        assertion = a_m.group(1).strip()
                    if r_m:
                        reason = r_m.group(1).strip()

            q_item = ExaminationQuestionItem(
                question_id=q.question_id,
                question_number=idx,
                section_name=sec_name,
                question_text=q.question_text,
                question_type=q.question_type,
                chapter_id=q.chapter_id,
                chapter_name=self._get_chapter_name(q.chapter_id),
                topic_id=q.topic_id,
                concept_ids=q.concept_ids,
                marks=q.marks,
                difficulty=q.difficulty,
                cognitive_level=q.cognitive_level,
                options=opts,
                passage=passage,
                assertion=assertion,
                reason=reason,
                diagram_url=q.answer_key.get("diagram_url") if isinstance(q.answer_key, dict) else None,
                has_internal_choice=False,
            )
            q_items.append(q_item)

        total_q = len(q_items)
        ans_count = len(saved_dict)
        marked_count = len(marked_list)
        unans_count = max(0, total_q - ans_count)

        return ExaminationSessionState(
            session_id=sess["session_id"],
            student_id=student_id,
            paper_title=sess["paper_title"],
            paper_code=tmpl["paper_code"] if tmpl else "086/2027",
            blueprint_id=sess["blueprint_id"],
            status=current_status,
            started_at=sess["started_at"],
            expires_at=sess["expires_at"],
            remaining_time_seconds=max(0, remaining_secs),
            duration_minutes=sess["duration_minutes"],
            total_marks=sess["total_marks"],
            total_questions=total_q,
            questions=q_items,
            saved_answers=saved_dict,
            marked_for_review=marked_list,
            answered_count=ans_count,
            marked_count=marked_count,
            unanswered_count=unans_count,
            server_time=now_dt.isoformat(),
        )

    def save_answer(
        self,
        session_id: str,
        student_id: str,
        req: SaveExamAnswerRequest,
    ) -> SaveExamAnswerResponse:
        """
        Saves a student answer in real-time.
        Guarantees transactional persistence against browser refreshes.
        """
        sess = self.exam_repo.get_session(session_id)
        if not sess:
            raise ValueError(f"Session {session_id} not found.")

        if sess["status"] != "IN_PROGRESS":
            raise ValueError(f"Cannot save answer: Examination is already {sess['status']}.")

        # Check timeout
        now_dt = datetime.now(timezone.utc)
        expires_at_dt = datetime.fromisoformat(sess["expires_at"].replace("Z", "+00:00"))
        remaining_secs = int((expires_at_dt - now_dt).total_seconds())

        if remaining_secs <= 0:
            self.submit_examination(session_id=session_id, student_id=student_id, is_timeout=True)
            raise ValueError("Examination duration has expired. Session has been auto-submitted.")

        # Determine question number and section
        tmpl = self.exam_repo.get_template(sess["template_id"]) if sess["template_id"] else None
        qids = json.loads(tmpl["questions_sequence_json"]) if tmpl and tmpl["questions_sequence_json"] else []
        bp = self.exam_repo.get_blueprint(sess["blueprint_id"])

        q_num = 1
        sec_name = "Section A"
        if req.question_id in qids:
            q_num = qids.index(req.question_id) + 1
            sec_name = self._determine_section_name(q_num, bp)

        # Save to database
        counts = self.exam_repo.save_or_update_answer(
            session_id=session_id,
            student_id=student_id,
            question_id=req.question_id,
            question_number=q_num,
            section_name=sec_name,
            submitted_answer=req.submitted_answer,
            is_marked_for_review=req.is_marked_for_review,
            time_spent_seconds=req.time_spent_seconds,
        )

        total_q = sess["total_questions"]
        answered = counts["answered"]
        marked = counts["marked"]
        unanswered = max(0, total_q - answered)

        return SaveExamAnswerResponse(
            session_id=session_id,
            question_id=req.question_id,
            is_saved=True,
            is_marked_for_review=req.is_marked_for_review,
            server_timestamp=now_dt.isoformat(),
            remaining_time_seconds=max(0, remaining_secs),
            answered_count=answered,
            unanswered_count=unanswered,
            marked_count=marked,
        )

    # --------------------------------------------------------------------------
    # 4. Examination Submission & Multi-Typology Evaluation
    # --------------------------------------------------------------------------
    def submit_examination(
        self,
        session_id: str,
        student_id: str = "STU-001",
        is_timeout: bool = False,
    ) -> ExaminationResultSummary:
        """
        Submits the examination, evaluates every response, updates the Learner Model,
        detects misconceptions, schedules spaced revisions, and stores full analytics.
        """
        sess = self.exam_repo.get_session(session_id)
        if not sess:
            raise ValueError(f"Session {session_id} not found.")

        # If already evaluated, return stored result
        if sess["status"] in ("SUBMITTED", "EVALUATED", "TIMED_OUT"):
            cached_result = self.get_examination_result(session_id, student_id)
            if cached_result:
                return cached_result

        bp = self.exam_repo.get_blueprint(sess["blueprint_id"])
        tmpl = self.exam_repo.get_template(sess["template_id"]) if sess["template_id"] else None
        qids = json.loads(tmpl["questions_sequence_json"]) if tmpl and tmpl["questions_sequence_json"] else []

        saved_answers_list = self.exam_repo.get_session_answers(session_id)
        ans_by_qid = {a["question_id"]: a for a in saved_answers_list}

        total_score = 0.0
        total_possible = float(sess["total_marks"])
        total_time_spent = sum(a.get("time_spent_seconds", 0) for a in saved_answers_list)

        section_scores: Dict[str, Dict[str, Any]] = {}
        unit_scores: Dict[str, Dict[str, Any]] = {}
        chapter_scores: Dict[str, Dict[str, Any]] = {}
        difficulty_scores: Dict[str, Dict[str, Any]] = {}
        cognitive_scores: Dict[str, Dict[str, Any]] = {}

        question_reviews: List[ExamQuestionReviewItem] = []
        tested_concepts = set()
        detected_misconceptions_list = []

        for idx, qid in enumerate(qids, start=1):
            q = self.question_repo.get_question(qid)
            if not q:
                continue

            sec_name = self._determine_section_name(idx, bp)
            ch_name = self._get_chapter_name(q.chapter_id)
            unit_name = self._get_unit_for_chapter(q.chapter_id)

            # Get submitted answer
            ans_record = ans_by_qid.get(qid)
            submitted_ans = ans_record.get("submitted_answer") if ans_record else None
            if submitted_ans is None:
                submitted_ans = {}

            # Evaluate response
            eval_res = self.evaluation_service.evaluate_answer(question=q, submitted_answer=submitted_ans)

            marks_awarded = eval_res.marks_awarded
            is_correct = eval_res.is_correct
            feedback = eval_res.feedback
            total_score += marks_awarded

            # Update answer record in database
            self.exam_repo.record_evaluated_answer(
                session_id=session_id,
                question_id=qid,
                is_correct=is_correct,
                marks_awarded=marks_awarded,
                feedback=feedback,
            )

            # Accumulate Section Stats
            if sec_name not in section_scores:
                section_scores[sec_name] = {"marks_obtained": 0.0, "total_marks": 0.0, "questions_count": 0, "correct_count": 0}
            section_scores[sec_name]["marks_obtained"] += marks_awarded
            section_scores[sec_name]["total_marks"] += q.marks
            section_scores[sec_name]["questions_count"] += 1
            if is_correct:
                section_scores[sec_name]["correct_count"] += 1

            # Accumulate Unit Stats
            if unit_name not in unit_scores:
                unit_scores[unit_name] = {"marks_obtained": 0.0, "total_marks": 0.0, "questions_count": 0, "correct_count": 0}
            unit_scores[unit_name]["marks_obtained"] += marks_awarded
            unit_scores[unit_name]["total_marks"] += q.marks
            unit_scores[unit_name]["questions_count"] += 1
            if is_correct:
                unit_scores[unit_name]["correct_count"] += 1

            # Accumulate Chapter Stats
            if q.chapter_id not in chapter_scores:
                chapter_scores[q.chapter_id] = {"name": ch_name, "marks_obtained": 0.0, "total_marks": 0.0, "correct_count": 0, "total_count": 0}
            chapter_scores[q.chapter_id]["marks_obtained"] += marks_awarded
            chapter_scores[q.chapter_id]["total_marks"] += q.marks
            chapter_scores[q.chapter_id]["total_count"] += 1
            if is_correct:
                chapter_scores[q.chapter_id]["correct_count"] += 1

            # Accumulate Difficulty Stats
            diff_key = q.difficulty.value
            if diff_key not in difficulty_scores:
                difficulty_scores[diff_key] = {"marks_obtained": 0.0, "total_marks": 0.0, "correct_count": 0, "total_count": 0}
            difficulty_scores[diff_key]["marks_obtained"] += marks_awarded
            difficulty_scores[diff_key]["total_marks"] += q.marks
            difficulty_scores[diff_key]["total_count"] += 1
            if is_correct:
                difficulty_scores[diff_key]["correct_count"] += 1

            # Accumulate Cognitive Stats
            cog_key = q.cognitive_level.value
            if cog_key not in cognitive_scores:
                cognitive_scores[cog_key] = {"marks_obtained": 0.0, "total_marks": 0.0, "correct_count": 0, "total_count": 0}
            cognitive_scores[cog_key]["marks_obtained"] += marks_awarded
            cognitive_scores[cog_key]["total_marks"] += q.marks
            cognitive_scores[cog_key]["total_count"] += 1
            if is_correct:
                cognitive_scores[cog_key]["correct_count"] += 1

            # Track concepts
            for cid in q.concept_ids:
                tested_concepts.add(cid)

            # Learner Model Integration: Update Concept Mastery
            self.learner_service.process_evaluated_answer(
                student_id=student_id,
                concept_ids=q.concept_ids,
                is_correct=is_correct,
                difficulty=q.difficulty.value,
                misconception_tags=q.misconception_tags,
            )

            # Misconception Engine Integration
            misc_items = self.misconception_service.analyze_student_answer(
                student_id=student_id,
                question_id=qid,
                submitted_answer=submitted_ans,
                is_correct=is_correct,
            )
            for m in misc_items:
                if m.misconception_tag not in detected_misconceptions_list:
                    detected_misconceptions_list.append(m.misconception_tag)

            # Spaced Repetition Integration
            for cid in q.concept_ids:
                try:
                    self.spaced_repetition_service.complete_revision(
                        student_id=student_id,
                        concept_id=cid,
                        is_correct=is_correct,
                        difficulty_rating="NORMAL",
                    )
                except Exception:
                    self.spaced_repetition_service.schedule_concept_review(
                        student_id=student_id,
                        concept_id=cid,
                        initial_interval_days=1 if not is_correct else 3,
                    )

            # Build review item
            correct_ans_repr = q.answer_key.get("correct_option") or q.answer_key.get("accepted_value") or q.answer_key.get("key_points")
            question_reviews.append(
                ExamQuestionReviewItem(
                    question_id=q.question_id,
                    question_number=idx,
                    section_name=sec_name,
                    question_text=q.question_text,
                    question_type=q.question_type,
                    chapter_id=q.chapter_id,
                    chapter_name=ch_name,
                    concept_ids=q.concept_ids,
                    marks=q.marks,
                    marks_awarded=marks_awarded,
                    is_correct=is_correct,
                    submitted_answer=submitted_ans,
                    correct_answer=correct_ans_repr,
                    explanation=q.explanation,
                    evaluation_feedback=feedback,
                    misconception_tags=q.misconception_tags,
                )
            )

        percentage = round((total_score / total_possible) * 100.0, 2) if total_possible > 0 else 0.0

        # Calculate percentages for sections and units
        for s in section_scores.values():
            s["percentage"] = round((s["marks_obtained"] / s["total_marks"]) * 100.0, 1) if s["total_marks"] > 0 else 0.0
        for u in unit_scores.values():
            u["percentage"] = round((u["marks_obtained"] / u["total_marks"]) * 100.0, 1) if u["total_marks"] > 0 else 0.0

        # Evaluate strong vs weak concepts from tested concepts
        strong_concepts = []
        weak_concepts = []
        all_masteries = self.learner_repo.get_all_concept_mastery(student_id)
        mastery_map = {m.concept_id: m for m in all_masteries}

        for cid in tested_concepts:
            m_item = mastery_map.get(cid)
            score = m_item.mastery_score if m_item else 0.5
            c_node = self.concept_repo.get_concept(cid)
            c_name = c_node.name if c_node else cid
            info = {"concept_id": cid, "name": c_name, "mastery_score": round(score, 2)}
            if score >= 0.75:
                strong_concepts.append(info)
            elif score < 0.60:
                weak_concepts.append(info)

        # Sort weak concepts by lowest score first
        weak_concepts.sort(key=lambda x: x["mastery_score"])

        # Recommended next action
        rec_action = {}
        if weak_concepts:
            target_c = weak_concepts[0]
            rec_action = {
                "action_type": "TARGETED_REMEDIATION",
                "concept_id": target_c["concept_id"],
                "concept_name": target_c["name"],
                "reason": f"Mastery in {target_c['name']} is at {int(target_c['mastery_score']*100)}%. Immediate revision recommended.",
                "url": f"#view-targeted-learning?concept={target_c['concept_id']}",
            }
        else:
            rec_action = {
                "action_type": "ADVANCED_PRACTICE",
                "reason": "Exceptional board readiness demonstrated. Proceed with timed Section D and Section E high-order practice.",
                "url": "#view-adaptive-practice",
            }

        # Update Session in DB
        new_status = ExaminationStatus.TIMED_OUT if is_timeout else ExaminationStatus.SUBMITTED
        self.exam_repo.update_session_completion(
            session_id=session_id,
            status=new_status,
            score=total_score,
            percentage=percentage,
            time_spent_seconds=total_time_spent,
            is_timeout=is_timeout,
        )

        # Store Result in DB
        self.exam_repo.store_result(
            session_id=session_id,
            student_id=student_id,
            total_marks=int(total_possible),
            score=total_score,
            percentage=percentage,
            section_scores=section_scores,
            unit_scores=unit_scores,
            chapter_scores=chapter_scores,
            difficulty_scores=difficulty_scores,
            cognitive_scores=cognitive_scores,
            strong_concepts=strong_concepts,
            weak_concepts=weak_concepts,
            misconceptions=detected_misconceptions_list,
            recommended_remediation=rec_action,
        )

        completed_at_iso = datetime.now(timezone.utc).isoformat()
        student = self.learner_repo.get_or_create_student(student_id)

        return ExaminationResultSummary(
            session_id=session_id,
            student_id=student_id,
            student_name=student.name,
            paper_title=sess["paper_title"],
            paper_code=tmpl["paper_code"] if tmpl else "086/2027",
            blueprint_id=sess["blueprint_id"],
            status=new_status,
            total_marks=int(total_possible),
            score=total_score,
            percentage=percentage,
            duration_minutes=sess["duration_minutes"],
            time_spent_seconds=total_time_spent,
            is_timeout_submission=is_timeout,
            section_scores=section_scores,
            unit_scores=unit_scores,
            chapter_scores=chapter_scores,
            difficulty_scores=difficulty_scores,
            cognitive_scores=cognitive_scores,
            strong_concepts=strong_concepts,
            weak_concepts=weak_concepts,
            detected_misconceptions=detected_misconceptions_list,
            recommended_next_action=rec_action,
            question_reviews=question_reviews,
            started_at=sess["started_at"],
            completed_at=completed_at_iso,
        )

    def get_examination_result(self, session_id: str, student_id: str) -> Optional[ExaminationResultSummary]:
        """Fetches stored result and builds rich ExaminationResultSummary."""
        stored = self.exam_repo.get_result_by_session(session_id)
        if not stored:
            return None

        sess = self.exam_repo.get_session(session_id)
        if not sess:
            return None

        tmpl = self.exam_repo.get_template(sess["template_id"]) if sess["template_id"] else None
        bp = self.exam_repo.get_blueprint(sess["blueprint_id"])
        qids = json.loads(tmpl["questions_sequence_json"]) if tmpl and tmpl["questions_sequence_json"] else []
        student = self.learner_repo.get_or_create_student(student_id)

        answers_list = self.exam_repo.get_session_answers(session_id)
        ans_by_qid = {a["question_id"]: a for a in answers_list}

        question_reviews = []
        for idx, qid in enumerate(qids, start=1):
            q = self.question_repo.get_question(qid)
            if not q:
                continue
            a = ans_by_qid.get(qid, {})
            sec_name = self._determine_section_name(idx, bp)
            ch_name = self._get_chapter_name(q.chapter_id)
            correct_ans_repr = q.answer_key.get("correct_option") or q.answer_key.get("accepted_value") or q.answer_key.get("key_points")

            question_reviews.append(
                ExamQuestionReviewItem(
                    question_id=q.question_id,
                    question_number=idx,
                    section_name=sec_name,
                    question_text=q.question_text,
                    question_type=q.question_type,
                    chapter_id=q.chapter_id,
                    chapter_name=ch_name,
                    concept_ids=q.concept_ids,
                    marks=q.marks,
                    marks_awarded=float(a.get("marks_awarded") or 0.0),
                    is_correct=bool(a.get("is_correct")),
                    submitted_answer=a.get("submitted_answer"),
                    correct_answer=correct_ans_repr,
                    explanation=q.explanation,
                    evaluation_feedback=a.get("evaluation_feedback"),
                    misconception_tags=q.misconception_tags,
                )
            )

        return ExaminationResultSummary(
            session_id=session_id,
            student_id=student_id,
            student_name=student.name,
            paper_title=sess["paper_title"],
            paper_code=tmpl["paper_code"] if tmpl else "086/2027",
            blueprint_id=sess["blueprint_id"],
            status=ExaminationStatus(sess["status"]),
            total_marks=stored["total_marks"],
            score=stored["score_obtained"],
            percentage=stored["percentage"],
            duration_minutes=sess["duration_minutes"],
            time_spent_seconds=sess.get("time_spent_seconds") or 0,
            is_timeout_submission=bool(sess.get("is_timeout_submission")),
            section_scores=stored["section_scores"],
            unit_scores=stored["unit_scores"],
            chapter_scores=stored["chapter_scores"],
            difficulty_scores=stored["difficulty_scores"],
            cognitive_scores=stored["cognitive_scores"],
            strong_concepts=stored["strong_concepts"],
            weak_concepts=stored["weak_concepts"],
            detected_misconceptions=stored["misconceptions_detected"],
            recommended_next_action=stored["recommended_remediation"],
            question_reviews=question_reviews,
            started_at=sess["started_at"],
            completed_at=stored.get("completed_at") or sess.get("submitted_at") or "",
        )

    # --------------------------------------------------------------------------
    # 5. Dashboard & History Reporting
    # --------------------------------------------------------------------------
    def get_student_examination_history(self, student_id: str) -> List[ExaminationOverviewItem]:
        """Returns exam history for student dashboard."""
        sessions = self.exam_repo.get_student_sessions(student_id, limit=20)
        items = []
        for s in sessions:
            tmpl = self.exam_repo.get_template(s["template_id"]) if s["template_id"] else None
            items.append(
                ExaminationOverviewItem(
                    session_id=s["session_id"],
                    blueprint_id=s["blueprint_id"],
                    paper_title=s["paper_title"],
                    paper_code=tmpl["paper_code"] if tmpl else "086/2027",
                    total_marks=s["total_marks"],
                    duration_minutes=s["duration_minutes"],
                    question_count=s["total_questions"],
                    status=ExaminationStatus(s["status"]),
                    score=s.get("score"),
                    percentage=s.get("percentage"),
                    completed_at=s.get("submitted_at"),
                    is_active=(s["status"] == "IN_PROGRESS"),
                )
            )
        return items

    def get_teacher_examinations_summary(self) -> Dict[str, Any]:
        """Provides cohort-wide examination analytics for the Teacher Dashboard."""
        results = self.exam_repo.get_all_results()
        if not results:
            return {
                "total_examinations_taken": 0,
                "cohort_average_score": 0.0,
                "cohort_average_percentage": 0.0,
                "pass_rate_percentage": 0.0,
                "highest_score": 0.0,
                "lowest_score": 0.0,
                "frequent_weak_concepts": [],
                "recent_examinations": [],
            }

        scores = [r["score_obtained"] for r in results]
        percentages = [r["percentage"] for r in results]
        passed = [p for p in percentages if p >= 33.0]  # CBSE 33% passing rule

        # Aggregate weak concepts across cohort
        weak_concept_counts = {}
        for r in results:
            weak_list = json.loads(r["weak_concepts_json"]) if r.get("weak_concepts_json") else []
            for w in weak_list:
                cid = w.get("concept_id") or w.get("name")
                cname = w.get("name", cid)
                if cid not in weak_concept_counts:
                    weak_concept_counts[cid] = {"concept_id": cid, "name": cname, "count": 0}
                weak_concept_counts[cid]["count"] += 1

        top_weak = sorted(weak_concept_counts.values(), key=lambda x: x["count"], reverse=True)[:5]

        recent = []
        for r in results[:10]:
            recent.append({
                "session_id": r["session_id"],
                "student_id": r["student_id"],
                "student_name": r.get("student_name", "Student"),
                "paper_title": r.get("paper_title", "Board Exam Simulation"),
                "score_obtained": r["score_obtained"],
                "total_marks": r["total_marks"],
                "percentage": r["percentage"],
                "completed_at": r["completed_at"],
            })

        return {
            "total_examinations_taken": len(results),
            "cohort_average_score": round(sum(scores) / len(scores), 1),
            "cohort_average_percentage": round(sum(percentages) / len(percentages), 1),
            "pass_rate_percentage": round((len(passed) / len(percentages)) * 100.0, 1),
            "highest_score": round(max(scores), 1),
            "lowest_score": round(min(scores), 1),
            "frequent_weak_concepts": top_weak,
            "recent_examinations": recent,
        }

    # --------------------------------------------------------------------------
    # Helper Methods
    # --------------------------------------------------------------------------
    def _determine_section_name(self, question_number: int, blueprint: Optional[ExaminationBlueprint]) -> str:
        if not blueprint or blueprint.blueprint_id != "BP-CBSE-X-SCI-2027":
            if question_number <= 8:
                return "Section A"
            elif question_number <= 11:
                return "Section B"
            else:
                return "Section C"

        # Official CBSE 39-question distribution
        if question_number <= 20:
            return "Section A"
        elif question_number <= 26:
            return "Section B"
        elif question_number <= 33:
            return "Section C"
        elif question_number <= 36:
            return "Section D"
        else:
            return "Section E"

    def _get_chapter_name(self, chapter_id: str) -> str:
        with self.db.get_connection() as conn:
            row = conn.execute("SELECT name FROM chapters WHERE chapter_id = ?;", (chapter_id,)).fetchone()
            return row["name"] if row else chapter_id

    def _get_unit_for_chapter(self, chapter_id: str) -> str:
        with self.db.get_connection() as conn:
            row = conn.execute(
                """
                SELECT u.name as unit_name
                FROM chapters c
                JOIN units u ON c.unit_id = u.unit_id
                WHERE c.chapter_id = ?;
                """,
                (chapter_id,),
            ).fetchone()
            return row["unit_name"] if row else "General Science"
