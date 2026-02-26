from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from uuid import UUID
from datetime import datetime

from app.models.enums import UserRole


class SignupRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    role: UserRole
    display_name: Optional[str] = None  # For instructors
    business_name: Optional[str] = None  # For studios


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
