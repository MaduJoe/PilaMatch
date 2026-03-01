from sqlalchemy import Column, String, Boolean, Integer, Numeric, DateTime, func, ForeignKey, JSON, Date
from sqlalchemy.orm import relationship

from app.db.session import Base
from app.models.base import UUIDMixin, TimestampMixin, GUID


class User(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "users"

    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    no_show_count = Column(Integer, default=0, nullable=False)
    is_suspended = Column(Boolean, default=False, nullable=False)

    # Identity verification
    phone = Column(String(20))
    phone_verified = Column(Boolean, default=False, nullable=False)
    identity_verified = Column(Boolean, default=False, nullable=False)  # Real-name verified
    business_number = Column(String(20))  # For studios
    business_verified = Column(Boolean, default=False, nullable=False)

    # Deposit system (보증금)
    deposit_balance = Column(Numeric(10, 2), default=0, nullable=False)  # Current deposit amount
    deposit_required = Column(Numeric(10, 2), default=30000, nullable=False)  # Early bird: 30,000원 (v2.0)
    deposit_first_paid_at = Column(DateTime)  # When first deposit was paid (v2.0)
    is_early_bird = Column(Boolean, default=False, nullable=False)  # Early bird user (v2.0)

    # Activity tracking (v2.0)
    last_active_at = Column(DateTime, default=func.now(), nullable=False)
    onboarding_completed = Column(Boolean, default=False, nullable=False)

    # Trust score (v3.0 - enhanced)
    trust_score = Column(Integer, default=40, nullable=False)  # 0-100, default 40 for new users
    trust_level = Column(String(20), default="새싹", nullable=False)  # 새싹/인증/전문/마스터

    # 약관 동의
    terms_agreed_at = Column(DateTime, nullable=True)       # 이용약관 동의 일시
    privacy_agreed_at = Column(DateTime, nullable=True)      # 개인정보 동의 일시

    # 계정 삭제 (soft-delete)
    deleted_at = Column(DateTime, nullable=True)             # soft-delete 일시
    deletion_scheduled_at = Column(DateTime, nullable=True)  # 영구 삭제 예정일 (deleted_at + 30일)

    # Premium membership (v2.1)
    membership_tier = Column(String(20), default="free", nullable=False)  # free, premium
    has_premium_badge = Column(Boolean, default=False, nullable=False)  # Visual badge indicator

    # Daily usage tracking (v3.0)
    daily_applications_today = Column(Integer, default=0, nullable=False)
    daily_views_today = Column(Integer, default=0, nullable=False)
    last_usage_reset_date = Column(Date, nullable=True)
    last_viewed_profiles = Column(JSON, nullable=True)  # List of viewed profile IDs today

    # Trust Tier system (v4.0)
    tier = Column(String(20), nullable=True)  # t1_basic/t2_verified/t3_pro or c1_basic/c2_verified
    tier_computed_at = Column(DateTime, nullable=True)
    suspension_until = Column(DateTime, nullable=True)  # Active suspension end
    restriction_until = Column(DateTime, nullable=True)  # Restriction end (e.g. today-class ban)

    # Relationships
    instructor_profile = relationship("InstructorProfile", back_populates="user", uselist=False)
    studio_profile = relationship("StudioProfile", back_populates="user", uselist=False)
    subscription = relationship("Subscription", back_populates="user", uselist=False)
    usage_limits = relationship("DailyUsageLimit", back_populates="user")
