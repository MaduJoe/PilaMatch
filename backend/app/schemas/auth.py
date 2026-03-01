import re

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from uuid import UUID
from datetime import datetime

from app.models.enums import UserRole


def _validate_password_complexity(password: str) -> str:
    """Validate password has at least 1 uppercase, 1 lowercase, and 1 digit."""
    if not re.search(r'[A-Z]', password):
        raise ValueError('비밀번호에 대문자가 1개 이상 포함되어야 합니다')
    if not re.search(r'[a-z]', password):
        raise ValueError('비밀번호에 소문자가 1개 이상 포함되어야 합니다')
    if not re.search(r'[0-9]', password):
        raise ValueError('비밀번호에 숫자가 1개 이상 포함되어야 합니다')
    return password


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    role: UserRole
    display_name: Optional[str] = None  # For instructors
    business_name: Optional[str] = None  # For studios

    @field_validator('password')
    @classmethod
    def password_complexity(cls, v: str) -> str:
        return _validate_password_complexity(v)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: Optional[str] = None
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: UUID
    email: str
    role: UserRole
    is_active: bool
    is_verified: bool
    no_show_count: int = 0
    is_suspended: bool = False

    # Profile names - populated from related profiles
    display_name: Optional[str] = None  # For instructors (from InstructorProfile)
    business_name: Optional[str] = None  # For studios (from StudioProfile)

    # Verification status
    phone_verified: bool = False
    identity_verified: bool = False
    business_verified: bool = False

    # v2.0 fields
    trust_score: int = 0
    last_active_at: Optional[datetime] = None
    onboarding_completed: bool = False

    class Config:
        from_attributes = True


class RefreshRequest(BaseModel):
    refresh_token: str


class MeResponse(BaseModel):
    user: UserResponse
    profile_id: Optional[UUID] = None


# --- Account Deletion ---

class AccountDeletionRequest(BaseModel):
    password: str  # 비밀번호 재확인


class AccountDeletionResponse(BaseModel):
    message: str
    deletion_scheduled_at: datetime


# --- Password Reset ---

class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)

    @field_validator('new_password')
    @classmethod
    def password_complexity(cls, v: str) -> str:
        return _validate_password_complexity(v)
