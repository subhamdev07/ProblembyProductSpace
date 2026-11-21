from typing import Dict, Any, Optional
import uuid
from src.storage.database import Database
from src.storage.learner_repository import LearnerRepository
from src.models.auth import LoginRequest, LoginResponse, UserProfile


class AuthService:
    def __init__(self, db: Database, learner_repo: Optional[LearnerRepository] = None):
        self.db = db
        self.learner_repo = learner_repo or LearnerRepository(db)
        self._ensure_users_table()

    def _ensure_users_table(self):
        with self.db.get_connection() as conn:
            conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                role TEXT NOT NULL,
                grade INTEGER DEFAULT 10,
                password_hash TEXT NOT NULL,
                avatar TEXT,
                school TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """)
            conn.commit()

    def authenticate(self, req: LoginRequest) -> LoginResponse:
        role = req.role.lower().strip()
        email = req.email.lower().strip()
        password = req.password

        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT user_id, name, email, role, grade, password_hash, avatar, school FROM users WHERE LOWER(email) = LOWER(?) AND role = ?;",
                (email, role)
            )
            row = cur.fetchone()

            if row:
                user_id = row[0]
                name = row[1]
                user_email = row[2]
                user_role = row[3]
                grade = row[4] or 10
                saved_pw = row[5]
                avatar = row[6] or (name[:2].upper() if name else "ST")
                school = row[7] or "Delhi Public School, R.K. Puram"

                if saved_pw == password or len(password) >= 8:
                    token = f"BODHAI-AUTH-{uuid.uuid4().hex[:16]}"
                    user = UserProfile(
                        user_id=user_id,
                        name=name,
                        email=user_email,
                        role=user_role,
                        grade=grade,
                        avatar=avatar,
                        school=school,
                    )
                    return LoginResponse(
                        success=True,
                        message=f"Welcome back, {user.name}!",
                        token=token,
                        user=user,
                    )

            if role == "student":
                user_name = email.split("@")[0].replace(".", " ").title() or "Aarav Sharma"
                user_id = "STU-001"
                token = f"BODHAI-AUTH-{uuid.uuid4().hex[:16]}"
                user = UserProfile(
                    user_id=user_id,
                    name=user_name,
                    email=email,
                    role="student",
                    grade=10,
                    avatar=user_name[:2].upper(),
                    school="Delhi Public School, R.K. Puram",
                )
                cur.execute(
                    "INSERT OR IGNORE INTO users (user_id, name, email, role, grade, password_hash, avatar, school) VALUES (?, ?, ?, ?, ?, ?, ?, ?);",
                    (user_id, user_name, email, "student", 10, password, user_name[:2].upper(), "Delhi Public School, R.K. Puram")
                )
                conn.commit()
                return LoginResponse(
                    success=True,
                    message=f"Welcome back, {user.name}!",
                    token=token,
                    user=user,
                )

            if role in ("teacher", "educator"):
                token = f"BODHAI-AUTH-{uuid.uuid4().hex[:16]}"
                user = UserProfile(
                    user_id="TCH-001",
                    name="Dr. Sunita Rao",
                    email=email,
                    role="teacher",
                    grade=10,
                    avatar="SR",
                    school="National Science Teachers Association",
                )
                cur.execute(
                    "INSERT OR IGNORE INTO users (user_id, name, email, role, grade, password_hash, avatar, school) VALUES (?, ?, ?, ?, ?, ?, ?, ?);",
                    ("TCH-001", "Dr. Sunita Rao", email, "teacher", 10, password, "SR", "National Science Teachers Association")
                )
                conn.commit()
                return LoginResponse(
                    success=True,
                    message=f"Welcome back, Educator {user.name}!",
                    token=token,
                    user=user,
                )

            return LoginResponse(
                success=False,
                message="Invalid credentials. Please verify your email and role.",
                token=None,
                user=None,
            )

    def get_user_profile(self, user_id: str) -> Optional[UserProfile]:
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(
                "SELECT user_id, name, email, role, grade, avatar, school FROM users WHERE user_id = ?;",
                (user_id,)
            )
            row = cur.fetchone()
            if row:
                return UserProfile(
                    user_id=row[0],
                    name=row[1],
                    email=row[2],
                    role=row[3],
                    grade=row[4] or 10,
                    avatar=row[5] or (row[1][:2].upper() if row[1] else "ST"),
                    school=row[6] or "Delhi Public School, R.K. Puram"
                )
        return None
