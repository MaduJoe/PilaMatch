from sqlalchemy import Column, String, Text, Boolean, ForeignKey, Numeric, Integer, JSON
from sqlalchemy.orm import relationship

from app.db.session import Base
from app.models.base import UUIDMixin, TimestampMixin, GUID


class StudioProfile(Base, UUIDMixin, TimestampMixin):
    __tablename__ = "studio_profiles"

    user_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    business_name = Column(String(200), nullable=False)
    description = Column(Text)
    phone = Column(String(20))
    address = Column(String(500))
    region = Column(String(100))
    logo_url = Column(String(500))
    categories = Column(JSON, default=[])
    photo_url = Column(String(500), nullable=True)
    is_verified = Column(Boolean, default=False, nullable=False)
    rating_average = Column(Numeric(3, 2), default=0)
    review_count = Column(Integer, default=0)
    location_proof_verified = Column(Boolean, default=False, nullable=False)  # C2 requirement

    # Relationships
    user = relationship("User", back_populates="studio_profile")
    job_posts = relationship("JobPost", back_populates="studio")
    reviews_received = relationship("Review", back_populates="reviewee_studio", foreign_keys="Review.reviewee_studio_id")
