"""Generic event log model for cross-domain audit trails.

Records domain events such as contract state changes, application submissions,
dispute actions, and other business-significant occurrences.  This complements
the existing ``ContractEventLog`` (which remains untouched for backward
compatibility) by providing a single, unified event store that any service
can write to.
"""

from sqlalchemy import Column, ForeignKey, JSON, String, Text

from app.db.session import Base
from app.models.base import GUID, UUIDMixin, TimestampMixin


class EventLog(Base, UUIDMixin, TimestampMixin):
    """Unified event log entry.

    Attributes:
        event_type: Dot-notation event identifier, e.g.
            ``"contract.status_changed"``, ``"application.submitted"``.
        actor_user_id: The user who triggered the event (nullable for
            system-generated events).
        target_type: The domain entity type affected, e.g. ``"contract"``,
            ``"user"``, ``"job_post"``.
        target_id: UUID (as string) of the affected entity.
        data: Free-form JSON metadata specific to the event type.
        note: Optional human-readable description.
    """

    __tablename__ = "event_logs"

    # Event classification
    event_type = Column(String(50), nullable=False, index=True)

    # Actor / target
    actor_user_id = Column(GUID(), ForeignKey("users.id"), nullable=True, index=True)
    target_type = Column(String(50), nullable=True)
    target_id = Column(String(36), nullable=True)

    # Payload
    data = Column(JSON, default=dict)
    note = Column(Text, nullable=True)
