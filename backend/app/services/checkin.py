"""GPS check-in service -- instructor arrival verification."""

import logging
from datetime import datetime
from decimal import Decimal

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.checkin_record import CheckinRecord
from app.models.job_post import JobPost
from app.models.application import Application
from app.models.instructor import InstructorProfile
from app.models.user import User
from app.utils.distance import haversine_distance
from app.services.event_log import EventLogService
from app.services.notification import NotificationService, NotificationType

logger = logging.getLogger(__name__)

VALID_CHECKIN_DISTANCE_M = 200  # meters

class CheckinService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def check_in(
        self,
        job_post_id: str,
        user_id: str,
        latitude: float,
        longitude: float,
    ) -> CheckinRecord:
        """Instructor GPS check-in at studio location.

        Validates that:
        1. Job post exists and has GPS coordinates
        2. User has an accepted application for this job
        3. No duplicate check-in exists

        Calculates Haversine distance (in meters) between instructor GPS and studio GPS.
        Marks is_valid=True if distance <= 200m.

        Updates instructor stats: total_checkins += 1, recalculates avg_checkin_distance_m.
        Sends notification to studio with check-in status.

        Returns CheckinRecord.
        Raises ValueError for not found / already checked in.
        """
        # Load job post
        job_result = await self.db.execute(
            select(JobPost).where(JobPost.id == job_post_id)
        )
        job_post = job_result.scalar_one_or_none()
        if not job_post:
            raise ValueError("JOB_POST_NOT_FOUND")
        if job_post.latitude is None or job_post.longitude is None:
            raise ValueError("JOB_POST_NO_GPS")

        # Find accepted application for this user
        # Need instructor_profile first
        profile_result = await self.db.execute(
            select(InstructorProfile).where(InstructorProfile.user_id == user_id)
        )
        instructor = profile_result.scalar_one_or_none()
        if not instructor:
            raise ValueError("INSTRUCTOR_NOT_FOUND")

        app_result = await self.db.execute(
            select(Application).where(
                and_(
                    Application.job_post_id == job_post_id,
                    Application.instructor_id == instructor.id,
                    Application.status == "accepted",
                )
            )
        )
        application = app_result.scalar_one_or_none()
        if not application:
            raise ValueError("NO_ACCEPTED_APPLICATION")

        # Check for duplicate check-in
        existing = await self.db.execute(
            select(CheckinRecord).where(
                and_(
                    CheckinRecord.job_post_id == job_post_id,
                    CheckinRecord.instructor_user_id == user_id,
                )
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError("ALREADY_CHECKED_IN")

        # Calculate distance in meters (haversine returns km)
        distance_km = haversine_distance(
            float(job_post.latitude), float(job_post.longitude),
            latitude, longitude,
        )
        distance_meters = distance_km * 1000
        is_valid = distance_meters <= VALID_CHECKIN_DISTANCE_M

        # Create record
        record = CheckinRecord(
            job_post_id=job_post_id,
            application_id=str(application.id),
            instructor_user_id=user_id,
            studio_latitude=job_post.latitude,
            studio_longitude=job_post.longitude,
            checkin_latitude=Decimal(str(latitude)),
            checkin_longitude=Decimal(str(longitude)),
            distance_meters=Decimal(str(round(distance_meters, 1))),
            is_valid=is_valid,
            checked_in_at=datetime.utcnow(),
        )
        self.db.add(record)

        # Update instructor stats
        instructor.total_checkins = (instructor.total_checkins or 0) + 1
        prev_avg = float(instructor.avg_checkin_distance_m or 0)
        prev_count = instructor.total_checkins - 1
        # Running average
        new_avg = ((prev_avg * prev_count) + distance_meters) / instructor.total_checkins
        instructor.avg_checkin_distance_m = Decimal(str(round(new_avg, 1)))

        await self.db.flush()

        # Notify studio
        try:
            from app.models.studio import StudioProfile
            studio_result = await self.db.execute(
                select(StudioProfile).where(StudioProfile.id == job_post.studio_id)
            )
            studio = studio_result.scalar_one_or_none()
            if studio:
                status_text = "도착" if is_valid else f"근처 ({int(distance_meters)}m)"
                notification_service = NotificationService(self.db)
                await notification_service.send(
                    user_id=str(studio.user_id),
                    type=NotificationType.LESSON_REMINDER,
                    title="강사 체크인",
                    body=f"강사님이 {status_text}했습니다. (거리: {int(distance_meters)}m)",
                    data={"job_post_id": job_post_id, "distance_meters": str(int(distance_meters))},
                )
        except Exception:
            logger.exception("Failed to send check-in notification")

        # Log event
        event_service = EventLogService(self.db)
        await event_service.log(
            event_type="checkin.completed",
            actor_user_id=user_id,
            target_type="job_post",
            target_id=job_post_id,
            data={"distance_meters": float(distance_meters), "is_valid": is_valid},
            note=f"Check-in {'valid' if is_valid else 'invalid'}: {int(distance_meters)}m",
        )

        return record

    async def get_checkin_status(
        self,
        job_post_id: str,
        user_id: str,
    ) -> dict:
        """Get check-in status for a specific job and user."""
        result = await self.db.execute(
            select(CheckinRecord).where(
                and_(
                    CheckinRecord.job_post_id == job_post_id,
                    CheckinRecord.instructor_user_id == user_id,
                )
            )
        )
        record = result.scalar_one_or_none()
        if not record:
            return {"checked_in": False}
        return {
            "checked_in": True,
            "is_valid": record.is_valid,
            "distance_meters": float(record.distance_meters),
            "checked_in_at": str(record.checked_in_at),
        }
