from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.models import Application, JobPost, InstructorProfile, StudioProfile, Offer, ApplicationStatus, JobPostStatus, User
from app.schemas.application import ApplicationCreate
from app.services.deposit import check_deposit_sufficient


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

        # v2.0: Check deposit on first application attempt
        # Get instructor's user_id
        instructor = await self.db.execute(
            select(InstructorProfile).where(InstructorProfile.id == instructor_id)
        )
        instructor = instructor.scalar_one_or_none()
        if instructor:
            # Check if user has any previous applications
            prev_apps = await self.db.execute(
                select(func.count(Application.id)).where(
                    Application.instructor_id == instructor_id
                )
            )
            app_count = prev_apps.scalar()

            # If this is the first application, check deposit
            if app_count == 0:
                has_sufficient_deposit = await check_deposit_sufficient(self.db, str(instructor.user_id))
                if not has_sufficient_deposit:
                    raise ValueError("INSUFFICIENT_DEPOSIT")

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
        self, instructor_id: UUID
    ) -> List[Tuple[Application, str, str]]:
        query = (
            select(Application, JobPost.title, StudioProfile.business_name)
            .join(JobPost, Application.job_post_id == JobPost.id)
            .join(StudioProfile, JobPost.studio_id == StudioProfile.id)
            .where(Application.instructor_id == instructor_id)
            .order_by(Application.created_at.desc())
        )

        result = await self.db.execute(query)
        return result.all()

    async def get_studio_profile_id(self, user_id: UUID) -> Optional[UUID]:
        result = await self.db.execute(
            select(StudioProfile.id).where(StudioProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_job_post(
        self, job_post_id: UUID, studio_id: UUID
    ) -> List[Tuple[Application, InstructorProfile, bool]]:
        """Get all applications for a job post (studio owner only).
        Returns tuples of (Application, InstructorProfile, has_offer)."""
        # Verify job post belongs to studio
        job_post = await self.db.execute(
            select(JobPost).where(
                JobPost.id == job_post_id,
                JobPost.studio_id == studio_id
            )
        )
        if not job_post.scalar_one_or_none():
            raise PermissionError("Not authorized to view applications for this job post")

        # Get applications with instructor info
        query = (
            select(Application, InstructorProfile)
            .join(InstructorProfile, Application.instructor_id == InstructorProfile.id)
            .where(Application.job_post_id == job_post_id)
            .order_by(Application.created_at.desc())
        )

        result = await self.db.execute(query)
        applications = result.all()

        # Check which applications have offers
        results = []
        for application, instructor in applications:
            offer_result = await self.db.execute(
                select(Offer.id).where(Offer.application_id == application.id)
            )
            has_offer = offer_result.scalar_one_or_none() is not None
            results.append((application, instructor, has_offer))

        return results

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
