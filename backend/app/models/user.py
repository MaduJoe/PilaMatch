from sqlalchemy import Column, String, Boolean, Integer, Numeric
from sqlalchemy.orm import relationship

from app.db.session import Base
from app.models.base import UUIDMixin, TimestampMixin


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
    deposit_required = Column(Numeric(10, 2), default=50000, nullable=False)  # Required deposit (5만원 default)

    # Relationships
    instructor_profile = relationship("InstructorProfile", back_populates="user", uselist=False)
    studio_profile = relationship("StudioProfile", back_populates="user", uselist=False)
