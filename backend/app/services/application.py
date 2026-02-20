from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.models import Application, JobPost, InstructorProfile, StudioProfile, Offer, ApplicationStatus, JobPostStatus, User
from app.schemas.application import ApplicationCreate
from app.services.profile_completeness import check_profile_completeness_for_action


class ApplicationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_instructor_profile_id(self, user_id: UUID) -> Optional[UUID]:
        result = await self.db.execute(
            select(InstructorProfile.id).where(InstructorProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id(self, application_id: UUID) -> Optional[Application]:
        result = await self.db.execute(
            select(Application).where(Application.id == application_id)
        )
        return result.scalar_one_or_none()

    async def create(
        self, job_post_id: UUID, instructor_id: UUID, data: ApplicationCreate
    ) -> Application:
        # Check if job post exists and is open
        job_post = await self.db.execute(
            select(JobPost).where(JobPost.id == job_post_id)
        )
        job_post = job_post.scalar_one_or_none()

        if not job_post:
            raise ValueError("Job post not found")

        if job_post.status != JobPostStatus.OPEN:
            raise ValueError("Job post is not open for applications")

        # Check for duplicate application
        existing = await self.db.execute(
            select(Application).where(
                Application.job_post_id == job_post_id,
                Application.instructor_id == instructor_id,
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError("DUPLICATE_APPLICATION")

        # v3.0: Check profile completeness instead of deposit
        instructor = await self.db.execute(
            select(InstructorProfile).where(InstructorProfile.id == instructor_id)
        )
        instructor = instructor.scalar_one_or_none()
        if instructor:
            completeness = await check_profile_completeness_for_action(
                self.db, str(instructor.user_id), "apply"
            )
            if not completeness["allowed"]:
                raise ValueError(f"INCOMPLETE_PROFILE:{completeness['reason']}")

            # v3.0 Phase 2: Check daily application limit
            from app.services.daily_usage import DailyUsageService
            from app.models.daily_usage import DailyUsageLimit

            daily_usage_service = DailyUsageService(self.db)
            usage_result = await daily_usage_service.check_and_increment_usage(
                instructor.user_id,
                DailyUsageLimit.UsageType.APPLICATION
            )

            if not usage_result["allowed"]:
                raise ValueError(f"APPLICATION_LIMIT:{usage_result['message']}")

        # Create application
        application = Application(
            job_post_id=job_post_id,
            instructor_id=instructor_id,
            status=ApplicationStatus.PENDING,
            cover_letter=data.cover_letter,
        )
        self.db.add(application)

        # Update application count
        job_post.application_count += 1

        await self.db.commit()
        await self.db.refresh(application)
        return application

    async def get_by_instructor(
        self, instructor_id: UUID, skip: int = 0, limit: int = 20
    ) -> Tuple[List[Tuple[Application, str, str]], int]:
        base_filter = Application.instructor_id == instructor_id

        # Count total
        count_result = await self.db.execute(
            select(func.count(Application.id)).where(base_filter)
        )
        total = count_result.scalar_one()

        query = (
            select(Application, JobPost.title, StudioProfile.business_name)
            .join(JobPost, Application.job_post_id == JobPost.id)
            .join(StudioProfile, JobPost.studio_id == StudioProfile.id)
            .where(base_filter)
            .order_by(Application.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        result = await self.db.execute(query)
        return result.all(), total

    async def get_studio_profile_id(self, user_id: UUID) -> Optional[UUID]:
        result = await self.db.execute(
            select(StudioProfile.id).where(StudioProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_job_post(
        self, job_post_id: UUID, studio_id: UUID, skip: int = 0, limit: int = 20
    ) -> Tuple[List[Tuple[Application, InstructorProfile, bool]], int]:
        """Get all applications for a job post (studio owner only).
        Returns tuples of (Application, InstructorProfile, has_offer) and total count."""
        # Verify job post belongs to studio
        job_post = await self.db.execute(
            select(JobPost).where(
                JobPost.id == job_post_id,
                JobPost.studio_id == studio_id
            )
        )
        if not job_post.scalar_one_or_none():
            raise PermissionError("Not authorized to view applications for this job post")

        base_filter = Application.job_post_id == job_post_id

        # Count total
        count_result = await self.db.execute(
            select(func.count(Application.id)).where(base_filter)
        )
        total = count_result.scalar_one()

        # Get applications with instructor info + pagination
        query = (
            select(Application, InstructorProfile)
            .join(InstructorProfile, Application.instructor_id == InstructorProfile.id)
            .where(base_filter)
            .order_by(Application.created_at.desc())
            .offset(skip)
            .limit(limit)
        )

        result = await self.db.execute(query)
        applications = result.all()

        # Batch-check offers to avoid N+1
        app_ids = [app.id for app, _ in applications]
        offers_result = await self.db.execute(
            select(Offer.application_id).where(Offer.application_id.in_(app_ids))
        )
        app_ids_with_offers = {row[0] for row in offers_result.all()}

        results = []
        for application, instructor in applications:
            has_offer = application.id in app_ids_with_offers
            results.append((application, instructor, has_offer))

        return results, total

    async def withdraw(self, application_id: UUID, instructor_id: UUID) -> Optional[Application]:
        application = await self.get_by_id(application_id)

        if not application:
            return None

        if application.instructor_id != instructor_id:
            raise PermissionError("Not authorized to withdraw this application")

        if application.status != ApplicationStatus.PENDING:
            raise ValueError("Can only withdraw pending applications")

        application.status = ApplicationStatus.WITHDRAWN

        # Update job post application count
        job_post = await self.db.execute(
            select(JobPost).where(JobPost.id == application.job_post_id)
        )
        job_post = job_post.scalar_one_or_none()
        if job_post and job_post.application_count > 0:
            job_post.application_count -= 1

        await self.db.commit()
        await self.db.refresh(application)
        return application

    async def get_active_application_count(self, instructor_id: UUID) -> int:
        """Get count of active (PENDING) applications for an instructor.

        v3.0 Phase 2: Used to display application limit status for Free tier users.
        """
        result = await self.db.execute(
            select(func.count(Application.id)).where(
                Application.instructor_id == instructor_id,
                Application.status == ApplicationStatus.PENDING
            )
        )
        return result.scalar_one() or 0
