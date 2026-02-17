from sqlalchemy import Column, String, Boolean, Integer, Numeric, DateTime, func, ForeignKey
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

    # Trust score (v2.0)
    trust_score = Column(Integer, default=0, nullable=False)

    # Premium membership (v2.1)
    membership_tier = Column(String(20), default="free", nullable=False)  # free, premium

    # Relationships
    instructor_profile = relationship("InstructorProfile", back_populates="user", uselist=False)
    studio_profile = relationship("StudioProfile", back_populates="user", uselist=False)
    subscription = relationship("Subscription", back_populates="user", uselist=False)
