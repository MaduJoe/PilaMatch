from sqlalchemy import Column, Text, Integer, Boolean, ForeignKey, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import relationship

from app.db.session import Base
from app.models.base import UUIDMixin, TimestampMixin, GUID


class Review(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "reviews"
    __table_args__ = (
        UniqueConstraint("contract_id", "reviewer_user_id", name="uq_review_contract_reviewer"),
        CheckConstraint("rating >= 1 AND rating <= 5", name="ck_review_rating_range"),
    )

    contract_id = Column(GUID(), ForeignKey("contracts.id", ondelete="CASCADE"), nullable=False, index=True)
    reviewer_user_id = Column(GUID(), ForeignKey("users.id"), nullable=False, index=True)
    reviewee_instructor_id = Column(GUID(), ForeignKey("instructor_profiles.id", ondelete="CASCADE"), index=True)
    reviewee_studio_id = Column(GUID(), ForeignKey("studio_profiles.id", ondelete="CASCADE"), index=True)
    rating = Column(Integer, nullable=False)
    comment = Column(Text)
    # Checklist review fields (PMF pivot - lightweight review)
    time_punctuality = Column(Boolean, nullable=True)   # 시간 준수
    professionalism = Column(Boolean, nullable=True)     # 전문성
    would_rehire = Column(Boolean, nullable=True)        # 재고용 의향

    # Relationships
    contract = relationship("Contract", back_populates="reviews")
    reviewee_instructor = relationship("InstructorProfile", back_populates="reviews_received", foreign_keys=[reviewee_instructor_id])
    reviewee_studio = relationship("StudioProfile", back_populates="reviews_received", foreign_keys=[reviewee_studio_id])
