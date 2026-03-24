"""Completion confirmation service -- mutual lesson completion verification."""

import logging
from datetime import datetime, timedelta
from decimal import Decimal

from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.completion_confirmation import CompletionConfirmation
from app.models.job_post import JobPost
from app.models.application import Application
from app.models.instructor import InstructorProfile
from app.models.user import User
from app.services.event_log import EventLogService

logger = logging.getLogger(__name__)

class CompletionService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def confirm_completion(
        self,
        job_post_id: str,
        user_id: str,
    ) -> CompletionConfirmation:
        """Confirm lesson completion (called by either studio or instructor).

        Creates or updates CompletionConfirmation:
        - If caller is studio: sets studio_confirmed=True
        - If caller is instructor: sets instructor_confirmed=True
        - If both confirmed: sets is_complete=True, updates instructor stats, re-evaluates tier

        Returns CompletionConfirmation.
        Raises ValueError if no accepted application found.
        """
        # Determine role (studio or instructor) from job_post ownership
        job_result = await self.db.execute(
            select(JobPost).where(JobPost.id == job_post_id)
        )
        job_post = job_result.scalar_one_or_none()
        if not job_post:
            raise ValueError("JOB_POST_NOT_FOUND")

        # Find the accepted application
        app_result = await self.db.execute(
            select(Application).where(
                and_(
                    Application.job_post_id == job_post_id,
                    Application.status == "accepted",
                )
            )
        )
        application = app_result.scalar_one_or_none()
        if not application:
            raise ValueError("NO_ACCEPTED_APPLICATION")

        # Get studio user_id
        from app.models.studio import StudioProfile
        studio_result = await self.db.execute(
            select(StudioProfile).where(StudioProfile.id == job_post.studio_id)
        )
        studio = studio_result.scalar_one_or_none()
        if not studio:
            raise ValueError("STUDIO_NOT_FOUND")

        # Get instructor user_id
        instructor_result = await self.db.execute(
            select(InstructorProfile).where(InstructorProfile.id == application.instructor_id)
        )
        instructor = instructor_result.scalar_one_or_none()
        if not instructor:
            raise ValueError("INSTRUCTOR_NOT_FOUND")

        # Determine caller role
        is_studio = str(user_id) == str(studio.user_id)
        is_instructor = str(user_id) == str(instructor.user_id)
        if not is_studio and not is_instructor:
            raise PermissionError("NOT_PARTICIPANT")

        # Get or create completion confirmation
        existing_result = await self.db.execute(
            select(CompletionConfirmation).where(
                CompletionConfirmation.job_post_id == job_post_id
            )
        )
        record = existing_result.scalar_one_or_none()

        now = datetime.utcnow()

        if not record:
            record = CompletionConfirmation(
                job_post_id=job_post_id,
                application_id=str(application.id),
                studio_user_id=str(studio.user_id),
                instructor_user_id=str(instructor.user_id),
                studio_confirmed=is_studio,
                instructor_confirmed=is_instructor,
                studio_confirmed_at=now if is_studio else None,
                instructor_confirmed_at=now if is_instructor else None,
            )
            self.db.add(record)
        else:
            if is_studio and not record.studio_confirmed:
                record.studio_confirmed = True
                record.studio_confirmed_at = now
            elif is_instructor and not record.instructor_confirmed:
                record.instructor_confirmed = True
                record.instructor_confirmed_at = now

        # Check if both confirmed
        if record.studio_confirmed and record.instructor_confirmed and not record.is_complete:
            record.is_complete = True
            await self._on_completion(instructor, user_id, job_post_id)

        await self.db.flush()

        # Log event
        role_str = "studio" if is_studio else "instructor"
        event_service = EventLogService(self.db)
        await event_service.log(
            event_type=f"completion.{role_str}_confirmed",
            actor_user_id=str(user_id),
            target_type="job_post",
            target_id=job_post_id,
            data={"is_complete": record.is_complete},
        )

        return record

    async def _on_completion(
        self,
        instructor: InstructorProfile,
        user_id: str,
        job_post_id: str,
    ) -> None:
        """Handle mutual completion: update stats and re-evaluate tier."""
        instructor.total_completions = (instructor.total_completions or 0) + 1
        instructor.completed_substitute_count = (instructor.completed_substitute_count or 0) + 1

        # Recalculate dispatch_success_rate
        total_dispatches = instructor.total_dispatches or 0
        if total_dispatches > 0:
            instructor.dispatch_success_rate = Decimal(
                str(round((instructor.total_dispatch_accepts or 0) / total_dispatches, 3))
            )

        await self.db.flush()

        # Re-evaluate tier
        try:
            from app.services.tier_evaluation import evaluate_and_update_tier
            await evaluate_and_update_tier(self.db, str(instructor.user_id))
        except Exception:
            logger.exception("Failed to re-evaluate tier after completion")

        # Log
        event_service = EventLogService(self.db)
        await event_service.log(
            event_type="completion.mutual_confirmed",
            actor_user_id=str(user_id),
            target_type="job_post",
            target_id=job_post_id,
            data={"total_completions": instructor.total_completions},
            note="Both parties confirmed lesson completion",
        )

    async def get_completion_status(
        self,
        job_post_id: str,
    ) -> dict:
        """Get completion status for a job."""
        result = await self.db.execute(
            select(CompletionConfirmation).where(
                CompletionConfirmation.job_post_id == job_post_id
            )
        )
        record = result.scalar_one_or_none()
        if not record:
            return {"exists": False, "is_complete": False}
        return {
            "exists": True,
            "studio_confirmed": record.studio_confirmed,
            "instructor_confirmed": record.instructor_confirmed,
            "is_complete": record.is_complete,
            "auto_completed": record.auto_completed,
            "studio_confirmed_at": str(record.studio_confirmed_at) if record.studio_confirmed_at else None,
            "instructor_confirmed_at": str(record.instructor_confirmed_at) if record.instructor_confirmed_at else None,
        }

    async def get_instructor_stats(
        self,
        instructor_user_id: str,
    ) -> dict:
        """Get instructor reliability stats (public-facing)."""
        result = await self.db.execute(
            select(InstructorProfile).where(InstructorProfile.user_id == instructor_user_id)
        )
        instructor = result.scalar_one_or_none()
        if not instructor:
            raise ValueError("INSTRUCTOR_NOT_FOUND")
        return {
            "dispatch_success_rate": float(instructor.dispatch_success_rate or 0),
            "total_dispatches": instructor.total_dispatches or 0,
            "total_dispatch_accepts": instructor.total_dispatch_accepts or 0,
            "total_completions": instructor.total_completions or 0,
            "total_checkins": instructor.total_checkins or 0,
            "avg_checkin_distance_m": float(instructor.avg_checkin_distance_m) if instructor.avg_checkin_distance_m else None,
        }


async def auto_complete_stale_records(db: AsyncSession) -> int:
    """Auto-complete records where one side confirmed but the other hasn't after 24h.

    Called periodically by background scheduler (every 1 hour).
    Returns count of auto-completed records.
    """
    now = datetime.utcnow()
    cutoff = now - timedelta(hours=24)
    count = 0

    # Studio confirmed, instructor not (after 24h)
    result = await db.execute(
        select(CompletionConfirmation).where(
            and_(
                CompletionConfirmation.is_complete.is_(False),
                CompletionConfirmation.studio_confirmed.is_(True),
                CompletionConfirmation.instructor_confirmed.is_(False),
                CompletionConfirmation.studio_confirmed_at < cutoff,
            )
        )
    )
    for record in result.scalars().all():
        record.instructor_confirmed = True
        record.instructor_confirmed_at = now
        record.is_complete = True
        record.auto_completed = True
        count += 1

    # Instructor confirmed, studio not (after 24h)
    result2 = await db.execute(
        select(CompletionConfirmation).where(
            and_(
                CompletionConfirmation.is_complete.is_(False),
                CompletionConfirmation.instructor_confirmed.is_(True),
                CompletionConfirmation.studio_confirmed.is_(False),
                CompletionConfirmation.instructor_confirmed_at < cutoff,
            )
        )
    )
    for record in result2.scalars().all():
        record.studio_confirmed = True
        record.studio_confirmed_at = now
        record.is_complete = True
        record.auto_completed = True
        count += 1

    if count > 0:
        await db.flush()
        logger.info("Auto-completed %d stale completion records", count)

    return count
