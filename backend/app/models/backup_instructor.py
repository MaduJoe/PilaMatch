"""Backup instructor model -- studio's trusted substitute pool."""
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.session import Base
from app.models.base import UUIDMixin, TimestampMixin, GUID


class BackupInstructor(Base, UUIDMixin, TimestampMixin):
    """Tracks which instructors a studio has saved to their backup network.

    Attributes:
        studio_id: The studio that owns this backup entry.
        instructor_id: The instructor saved as a backup.
        nickname: Optional studio-side nickname for quick identification.
        note: Free-text memo about the instructor.
        priority: 1=primary, 2=secondary, 3=general.
        last_worked_at: Last date this instructor completed a job for the studio.
        total_completed: Running count of completed jobs for this studio.
    """

    __tablename__ = "backup_instructors"
    __table_args__ = (
        UniqueConstraint("studio_id", "instructor_id", name="uq_backup_studio_instructor"),
    )

    studio_id = Column(
        GUID(),
        ForeignKey("studio_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    instructor_id = Column(
        GUID(),
        ForeignKey("instructor_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    nickname = Column(String(50))
    note = Column(Text)
    priority = Column(Integer, default=3)  # 1=primary, 2=secondary, 3=general
    last_worked_at = Column(DateTime, nullable=True)
    total_completed = Column(Integer, default=0)

    # Relationships
    studio = relationship("StudioProfile")
    instructor = relationship("InstructorProfile")
