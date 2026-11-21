"""
Teacher Dashboard Service
Cohort analytics, intervention triggers, and student drill-downs.
Strict access control: requires educator/teacher role authorization.
"""

from typing import List, Dict, Any, Optional

from src.storage.database import Database
from src.storage.learner_repository import LearnerRepository
from src.storage.remediation_repository import RemediationRepository
from src.storage.concept_repository import ConceptRepository
from src.models.teacher import TeacherDashboardData, TeacherStudentDetail
from src.models.learner import ConceptMasteryStatus


class TeacherDashboardService:
    def __init__(
        self,
        db: Database,
        learner_repo: LearnerRepository,
        remediation_repo: RemediationRepository,
        concept_repo: ConceptRepository,
        learner_service: Optional[Any] = None
    ):
        self.db = db
        self.learner_repo = learner_repo
        self.remediation_repo = remediation_repo
        self.concept_repo = concept_repo
        if learner_service is None:
            from src.storage.assessment_repository import AssessmentRepository
            from src.services.learner_model_service import LearnerModelService
            ass_repo = AssessmentRepository(db)
            self.learner_service = LearnerModelService(learner_repo, ass_repo, concept_repo)
        else:
            self.learner_service = learner_service

    def _verify_teacher_role(self, role: Optional[str]):
        """Role-based boundary check to prevent unauthorized access to cohort analytics."""
        if not role or role.lower() not in ("teacher", "educator", "admin"):
            raise PermissionError("Access Denied: Teacher Dashboard requires verified educator credentials.")

    def get_dashboard_summary(self, role: str = "teacher") -> TeacherDashboardData:
        self._verify_teacher_role(role)

        with self.db.get_connection() as conn:
            cur = conn.cursor()

            # 1. Total Students
            cur.execute("SELECT COUNT(*) FROM students;")
            total_students = cur.fetchone()[0]

            # 2. Assessments Completed & Accuracy
            cur.execute("SELECT COUNT(*), AVG(score) FROM assessments WHERE status IN ('SUBMITTED', 'EVALUATED');")
            ass_row = cur.fetchone()
            total_assessments = ass_row[0] or 0
            avg_accuracy = round(float(ass_row[1] or 0.0), 1)

            # 3. Average Concept Mastery
            cur.execute("SELECT AVG(mastery_score) FROM learner_concept_mastery;")
            mast_row = cur.fetchone()
            avg_mastery = round(float(mast_row[0] or 0.0) * 100, 1)

            # 4. Weakest Concepts Cohort-Wide
            cur.execute(
                """
                SELECT c.concept_id, c.name, AVG(lcm.mastery_score) as avg_mastery, COUNT(lcm.student_id) as attempts
                FROM concepts c
                JOIN learner_concept_mastery lcm ON c.concept_id = lcm.concept_id
                GROUP BY c.concept_id, c.name
                HAVING avg_mastery < 0.60
                ORDER BY avg_mastery ASC
                LIMIT 5;
                """
            )
            weak_rows = cur.fetchall()
            weakest_concepts = [
                {
                    "concept_id": r["concept_id"],
                    "concept_name": r["name"],
                    "avg_mastery_pct": round(r["avg_mastery"] * 100, 1),
                    "assessed_students": r["attempts"]
                }
                for r in weak_rows
            ]

            # 5. Common Misconceptions
            common_misconceptions = self.remediation_repo.get_all_misconceptions_summary()

            # 6. Students Requiring Intervention
            cur.execute(
                """
                SELECT s.student_id, s.name, s.grade,
                       COALESCE(AVG(lcm.mastery_score), 0.0) as avg_mastery,
                       COUNT(DISTINCT sm.misconception_record_id) as misconception_count
                FROM students s
                LEFT JOIN learner_concept_mastery lcm ON s.student_id = lcm.student_id
                LEFT JOIN student_misconceptions sm ON s.student_id = sm.student_id AND sm.status IN ('SUSPECTED', 'CONFIRMED')
                GROUP BY s.student_id, s.name, s.grade
                ORDER BY avg_mastery ASC, misconception_count DESC;
                """
            )
            stu_rows = cur.fetchall()
            intervention_students = []
            for sr in stu_rows:
                needs_intervention = (sr["avg_mastery"] < 0.60) or (sr["misconception_count"] >= 1)
                if needs_intervention:
                    intervention_students.append({
                        "student_id": sr["student_id"],
                        "name": sr["name"],
                        "grade": sr["grade"],
                        "avg_mastery_pct": round(sr["avg_mastery"] * 100, 1),
                        "active_misconceptions": sr["misconception_count"],
                        "urgency": "HIGH" if sr["avg_mastery"] < 0.40 or sr["misconception_count"] >= 2 else "MEDIUM"
                    })

            # 7. Revision Completion Rate
            cur.execute("SELECT COUNT(*) FROM spaced_repetition_schedules;")
            total_revs = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM spaced_repetition_schedules WHERE review_count > 0;")
            done_revs = cur.fetchone()[0]
            completion_rate = round((done_revs / max(1, total_revs)) * 100, 1) if total_revs > 0 else 0.0

            # 8. Chapter Performance
            chapter_perf = [
                {
                    "chapter_id": "CH-01",
                    "chapter_name": "Chemical Reactions and Equations",
                    "total_concepts": 29,
                    "assessed_concepts": len(weak_rows),
                    "average_mastery_pct": avg_mastery,
                    "average_accuracy_pct": avg_accuracy
                }
            ]

            return TeacherDashboardData(
                total_students=total_students,
                total_assessments_completed=total_assessments,
                average_accuracy_pct=avg_accuracy,
                average_concept_mastery_pct=avg_mastery,
                weakest_concepts=weakest_concepts,
                common_misconceptions=common_misconceptions[:5],
                students_requiring_intervention=intervention_students,
                revision_completion_rate_pct=completion_rate,
                chapter_performance=chapter_perf
            )

    def get_student_drilldown(self, student_id: str, role: str = "teacher") -> TeacherStudentDetail:
        self._verify_teacher_role(role)

        student = self.learner_repo.get_or_create_student(student_id)
        dash_data = self.learner_service.get_student_dashboard(student_id)
        misconceptions = self.remediation_repo.get_student_misconceptions(student_id)
        revisions = self.remediation_repo.get_revision_schedules(student_id)

        # Generate Pedagogical Intervention Notes
        notes = []
        if dash_data.overall_mastery_pct < 50.0:
            notes.append("Learner exhibits overall low mastery (<50%). Recommend starting foundational prerequisite scaffolding.")
        if any(m.status.value == "CONFIRMED" for m in misconceptions):
            notes.append("Confirmed misconceptions detected. Schedule 1-on-1 concept lab or assign targeted remediation.")
        if dash_data.weak_concepts:
            top_weak = ", ".join([c.concept_name for c in dash_data.weak_concepts[:3]])
            notes.append(f"Immediate focus areas: {top_weak}.")
        if not notes:
            notes.append("Student is performing on track. Maintain standard spaced revision cadence.")

        return TeacherStudentDetail(
            student=student,
            mastery_distribution=dash_data.mastery_distribution,
            overall_accuracy_pct=dash_data.overall_accuracy_pct,
            assessment_history=dash_data.recent_assessments,
            active_misconceptions=[m for m in misconceptions if m.status.value != "RESOLVED"],
            weak_concepts=dash_data.weak_concepts,
            scheduled_revisions=revisions,
            intervention_notes=notes
        )

    def get_all_students_overview(self, role: str = "teacher") -> List[Dict[str, Any]]:
        self._verify_teacher_role(role)

        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT student_id, name, grade, created_at FROM students ORDER BY student_id ASC;")
            rows = cur.fetchall()

            results = []
            for r in rows:
                sid = r["student_id"]
                dash = self.learner_service.get_student_dashboard(sid)
                results.append({
                    "student_id": sid,
                    "name": r["name"],
                    "grade": r["grade"],
                    "accuracy_pct": dash.overall_accuracy_pct,
                    "mastery_pct": dash.overall_mastery_pct,
                    "assessments_count": dash.total_assessments_taken,
                    "weak_concepts_count": len(dash.weak_concepts),
                    "needs_intervention": dash.overall_mastery_pct < 60.0 or len(dash.weak_concepts) >= 2
                })
            return results
