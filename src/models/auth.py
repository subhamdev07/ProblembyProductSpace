"""
Authentication Models for BodhAI
Supports role-based session initiation for Students and Educators.
"""

from typing import Optional
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., description="User password")
    role: str = Field("student", description="Account role: student or teacher")


class UserProfile(BaseModel):
    user_id: str
    name: str
    email: str
    role: str
    grade: Optional[int] = 10
    avatar: str
    school: str = "Delhi Public School, R.K. Puram"


class LoginResponse(BaseModel):
    success: bool
    message: str
    token: str
    user: UserProfile
