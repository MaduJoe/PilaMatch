"""Policy agreement tracking model (v2.0)."""
from sqlalchemy import Column, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.db.session import Base
from app.models.base import UUIDMixin, GUID


class PolicyType(str):
    TERMS_OF_SERVICE = "terms_of_service"  # Service terms
    PRIVACY = "privacy"  # Privacy policy
    REFUND = "refund"  # Refund/cancellation policy
    ESCROW = "escrow"  # Escrow payment terms
    MARKETING = "marketing"  # Marketing consent (optional)
    LOCATION = "location"  # Location usage (optional, future)


class PolicyAgreement(Base, UUIDMixin):
    """Track user agreements to various policies and terms."""
    __tablename__ = "policy_agreements"

    user_id = Column(GUID(), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    policy_type = Column(String(50), nullable=False)  # PolicyType
    policy_version = Column(String(10), nullable=False)  # e.g., "1.0", "2.0"
    agreed_at = Column(DateTime, nullable=False)

    # Relationships
    user = relationship("User", foreign_keys=[user_id])