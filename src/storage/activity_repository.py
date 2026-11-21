import json
import uuid
from typing import List, Dict, Any, Optional
from src.storage.database import Database
from src.models.activity import StudentActivityLog, StudentTelemetrySummary


class ActivityRepository:
    def __init__(self, db: Database):
        self.db = db

    def log_activity(
        self,
        student_id: str,
        event_type: str,
        action_title: str,
        details: Optional[Dict[str, Any]] = None,
        duration_seconds: int = 0,
    ) -> str:
        log_id = f"ACT-{uuid.uuid4().hex[:12].upper()}"
        details_json = json.dumps(details or {}, ensure_ascii=False)

        conn = self.db.get_connection()
        try:
            conn.execute("INSERT OR IGNORE INTO students (student_id, name, grade) VALUES (?, ?, 10);", (student_id, student_id))
            conn.execute(
                """
                INSERT INTO student_activity_logs (
                    log_id, student_id, event_type, action_title, details_json, duration_seconds
                ) VALUES (?, ?, ?, ?, ?, ?);
                """,
                (log_id, student_id, event_type, action_title, details_json, duration_seconds),
            )
            conn.commit()
        finally:
            conn.close()

        return log_id

    def get_student_activities(
        self, student_id: str, limit: int = 50
    ) -> List[StudentActivityLog]:
        conn = self.db.get_connection()
        try:
            rows = conn.execute(
                """
                SELECT log_id, student_id, event_type, action_title, details_json, duration_seconds, created_at
                FROM student_activity_logs
                WHERE student_id = ?
                ORDER BY created_at DESC
                LIMIT ?;
                """,
                (student_id, limit),
            ).fetchall()

            activities = []
            for r in rows:
                try:
                    dt = json.loads(r["details_json"])
                except Exception:
                    dt = {}
                activities.append(
                    StudentActivityLog(
                        log_id=r["log_id"],
                        student_id=r["student_id"],
                        event_type=r["event_type"],
                        action_title=r["action_title"],
                        details=dt,
                        duration_seconds=r["duration_seconds"] or 0,
                        created_at=str(r["created_at"]),
                    )
                )
            return activities
        finally:
            conn.close()

    def get_all_activities(self, limit: int = 100) -> List[Dict[str, Any]]:
        conn = self.db.get_connection()
        try:
            rows = conn.execute(
                """
                SELECT log_id, student_id, event_type, action_title, details_json, duration_seconds, created_at
                FROM student_activity_logs
                ORDER BY created_at DESC
                LIMIT ?;
                """,
                (limit,),
            ).fetchall()

            result = []
            for r in rows:
                try:
                    dt = json.loads(r["details_json"])
                except Exception:
                    dt = {}
                result.append({
                    "log_id": r["log_id"],
                    "student_id": r["student_id"],
                    "event_type": r["event_type"],
                    "action_title": r["action_title"],
                    "details": dt,
                    "duration_seconds": r["duration_seconds"] or 0,
                    "created_at": str(r["created_at"]),
                })
            return result
        finally:
            conn.close()

    def get_student_telemetry_summary(
        self, student_id: str, student_name: str = "Student"
    ) -> StudentTelemetrySummary:
        conn = self.db.get_connection()
        try:
            cur = conn.cursor()

            cur.execute("SELECT COUNT(*) FROM student_activity_logs WHERE student_id = ?;", (student_id,))
            total_actions = cur.fetchone()[0]

            cur.execute(
                "SELECT COALESCE(SUM(duration_seconds), 0) FROM student_activity_logs WHERE student_id = ?;",
                (student_id,),
            )
            total_time = cur.fetchone()[0]

            cur.execute(
                """
                SELECT event_type, COUNT(*) as cnt
                FROM student_activity_logs
                WHERE student_id = ?
                GROUP BY event_type;
                """,
                (student_id,),
            )
            event_breakdown = {r["event_type"]: r["cnt"] for r in cur.fetchall()}

            cur.execute(
                "SELECT created_at FROM student_activity_logs WHERE student_id = ? ORDER BY created_at DESC LIMIT 1;",
                (student_id,),
            )
            last_row = cur.fetchone()
            last_active = str(last_row[0]) if last_row else None

            recent_activities = self.get_student_activities(student_id, limit=10)

            return StudentTelemetrySummary(
                student_id=student_id,
                student_name=student_name,
                total_actions_logged=total_actions,
                total_time_spent_seconds=total_time,
                last_active_at=last_active,
                event_type_breakdown=event_breakdown,
                recent_activities=recent_activities,
            )
        finally:
            conn.close()
