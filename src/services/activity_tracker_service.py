from typing import List, Dict, Any, Optional
from src.storage.database import Database
from src.storage.activity_repository import ActivityRepository
from src.models.activity import StudentActivityLog, StudentTelemetrySummary, RecordActivityRequest


class ActivityTrackerService:
    def __init__(self, db: Database, activity_repo: Optional[ActivityRepository] = None):
        self.db = db
        self.repo = activity_repo or ActivityRepository(db)

    def record_event(
        self,
        student_id: str,
        event_type: str,
        action_title: str,
        details: Optional[Dict[str, Any]] = None,
        duration_seconds: int = 0,
    ) -> str:
        try:
            return self.repo.log_activity(
                student_id=student_id,
                event_type=event_type,
                action_title=action_title,
                details=details or {},
                duration_seconds=duration_seconds,
            )
        except Exception as e:
            return "LOG_ERROR"

    def get_timeline(self, student_id: str, limit: int = 50) -> List[StudentActivityLog]:
        return self.repo.get_student_activities(student_id, limit=limit)

    def get_classroom_feed(self, limit: int = 100) -> List[Dict[str, Any]]:
        return self.repo.get_all_activities(limit=limit)

    def get_summary(self, student_id: str, student_name: str = "Student") -> StudentTelemetrySummary:
        return self.repo.get_student_telemetry_summary(student_id, student_name)
