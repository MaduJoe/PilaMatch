import enum


class UserRole(str, enum.Enum):
    INSTRUCTOR = "instructor"
    STUDIO = "studio"
    ADMIN = "admin"


class MembershipTier(str, enum.Enum):
    """Membership tier levels."""
    FREE = "free"
    PREMIUM = "premium"


class Category(str, enum.Enum):
    PILATES = "pilates"
    YOGA = "yoga"


class JobType(str, enum.Enum):
    SUBSTITUTE = "substitute"
    REGULAR = "regular"
    CONTRACT = "contract"


class JobPostStatus(str, enum.Enum):
    OPEN = "open"
    CLOSED = "closed"
    FILLED = "filled"


class ApplicationStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"


class OfferStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    EXPIRED = "expired"


class ContractStatus(str, enum.Enum):
    CONFIRMED = "confirmed"
    IN_PROGRESS = "in_progress"
    PENDING_COMPLETION = "pending_completion"  # v2.0: Waiting for both parties to confirm
    COMPLETED = "completed"
    DISPUTED = "disputed"  # v2.0: Completion rejected, entering dispute
    CANCELLED = "cancelled"


class ThreadScope(str, enum.Enum):
    JOB = "job"
    CONTRACT = "contract"


class MessageType(str, enum.Enum):
    TEXT = "text"
    SYSTEM = "system"


class ReportType(str, enum.Enum):
    HARASSMENT = "harassment"
    NO_SHOW = "no_show"
    FRAUD = "fraud"
    OTHER = "other"


class ReportStatus(str, enum.Enum):
    OPEN = "open"
    UNDER_REVIEW = "under_review"
    RESOLVED = "resolved"
    DISMISSED = "dismissed"


class TicketStatus(str, enum.Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class SubscriptionStatus(str, enum.Enum):
    """Subscription status types."""
    INACTIVE = "inactive"  # Created but not paid yet
    ACTIVE = "active"      # Paid and active
    CANCELLED = "cancelled"  # User cancelled, will expire at end of period
    EXPIRED = "expired"    # Past end date
    SUSPENDED = "suspended"  # Payment failed after retries


class SubscriptionPaymentStatus(str, enum.Enum):
    """Payment status specifically for subscription payments."""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class SubscriptionChangeReason(str, enum.Enum):
    """Reasons for subscription changes."""
    UPGRADE = "upgrade"
    DOWNGRADE = "downgrade"
    AUTO_RENEW = "auto_renew"
    CANCELLATION = "cancellation"
    SUSPENSION = "suspension"
    REACTIVATION = "reactivation"


class TeacherTier(str, enum.Enum):
    T1_BASIC = "t1_basic"
    T2_VERIFIED = "t2_verified"
    T3_PRO = "t3_pro"


class CenterTier(str, enum.Enum):
    C1_BASIC = "c1_basic"
    C2_VERIFIED = "c2_verified"
    # C3_TRUSTED = "c3_trusted"  # Post-MVP


class PenaltyType(str, enum.Enum):
    NO_SHOW = "no_show"
    SAME_DAY_CANCEL = "same_day_cancel"
    LATE = "late"
    CANCEL_AFTER_CONFIRM = "cancel_after_confirm"


class PenaltyStatus(str, enum.Enum):
    ACTIVE = "active"
    EXPIRED = "expired"


class PaymentConfirmationStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    DISPUTED = "disputed"
