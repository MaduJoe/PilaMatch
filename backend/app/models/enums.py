import enum


class UserRole(str, enum.Enum):
    INSTRUCTOR = "instructor"
    STUDIO = "studio"
    ADMIN = "admin"


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
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class PaymentStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class PayoutStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


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
