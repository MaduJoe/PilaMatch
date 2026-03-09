import datetime as dt
from typing import Optional, List
from uuid import UUID
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload

from app.models import (
    Review, Application, JobPost, InstructorProfile, StudioProfile, UserRole
)
from app.schemas.review import ReviewCreate, ReviewUpdate

KST_OFFSET = dt.timedelta(hours=9)


class ReviewService:
    def __init__(self, db: AsyncSession):
        self.db = db

    # -- Profile lookups -------------------------------------------------------

    async def get_studio_profile_id(self, user_id: UUID) -> Optional[UUID]:
        result = await self.db.execute(
            select(StudioProfile.id).where(StudioProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_instructor_profile_id(self, user_id: UUID) -> Optional[UUID]:
        result = await self.db.execute(
            select(InstructorProfile.id).where(InstructorProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    # -- Time window -----------------------------------------------------------

    @staticmethod
    def _review_window(job_post: JobPost) -> tuple[dt.datetime, dt.datetime]:
        """Returns (window_open_utc, window_close_utc) for a job post.

        Class times stored as KST. Review opens at class end_time,
        closes at 23:59:59 KST on the class date.
        """
        class_date: dt.date = job_post.date
        end_time: dt.time = job_post.end_time

        # Class end in KST -> UTC
        end_kst = dt.datetime.combine(class_date, end_time)
        end_utc = end_kst - KST_OFFSET

        # Deadline: 23:59:59 KST on class date -> UTC
        eod_kst = dt.datetime.combine(class_date, dt.time(23, 59, 59))
        eod_utc = eod_kst - KST_OFFSET

        return end_utc, eod_utc

    def check_review_window(self, job_post: JobPost) -> tuple[bool, bool]:
        """Returns (is_eligible, is_expired)."""
        now_utc = dt.datetime.utcnow()
        window_open, window_close = self._review_window(job_post)
        is_eligible = now_utc >= window_open
        is_expired = now_utc > window_close
        return is_eligible, is_expired

    # -- Create review (application-anchored) ----------------------------------

    async def create_review(
        self,
        application_id: UUID,
        reviewer_user_id: UUID,
        reviewer_role: str,
        data: ReviewCreate,
    ) -> Review:
        # Load application with job post
        result = await self.db.execute(
            select(Application)
            .options(joinedload(Application.job_post))
            .where(Application.id == application_id)
        )
        application = result.unique().scalar_one_or_none()

        if not application:
            raise ValueError("Application not found")

        if not application.contact_revealed:
            raise ValueError("Cannot review: application not accepted")

        job_post = application.job_post
        if not job_post:
            raise ValueError("Job post not found")

        # Check time window
        is_eligible, is_expired = self.check_review_window(job_post)
        if not is_eligible:
            raise ValueError("수업이 아직 종료되지 않았습니다")
        if is_expired:
            raise ValueError("리뷰 작성 가능 기간이 지났습니다")

        # IDOR check: verify reviewer is a party to this application
        if reviewer_role == UserRole.STUDIO:
            studio_id = await self.get_studio_profile_id(reviewer_user_id)
            if not studio_id or str(job_post.studio_id) != str(studio_id):
                raise PermissionError("Not authorized to review this application")
            reviewee_instructor_id = application.instructor_id
            reviewee_studio_id = None
        else:
            instructor_id = await self.get_instructor_profile_id(reviewer_user_id)
            if not instructor_id or str(application.instructor_id) != str(instructor_id):
                raise PermissionError("Not authorized to review this application")
            reviewee_instructor_id = None
            reviewee_studio_id = job_post.studio_id

        # Duplicate check
        existing = await self.db.execute(
            select(Review).where(
                Review.application_id == application_id,
                Review.reviewer_user_id == reviewer_user_id,
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError("이미 리뷰를 작성했습니다")

        # Create review
        review = Review(
            application_id=application_id,
            contract_id=None,
            reviewer_user_id=reviewer_user_id,
            reviewee_instructor_id=reviewee_instructor_id,
            reviewee_studio_id=reviewee_studio_id,
            rating=data.rating,
            comment=data.comment,
            time_punctuality=data.time_punctuality,
            professionalism=data.professionalism,
            would_rehire=data.would_rehire,
        )
        self.db.add(review)
        await self.db.flush()  # make new row visible for avg recalculation

        # Update average rating
        if reviewee_instructor_id:
            await self._update_instructor_rating(reviewee_instructor_id)
        if reviewee_studio_id:
            await self._update_studio_rating(reviewee_studio_id)

        await self.db.commit()
        await self.db.refresh(review)
        return review

    # -- Rating updates --------------------------------------------------------

    async def _update_instructor_rating(self, instructor_id: UUID) -> None:
        result = await self.db.execute(
            select(
                func.avg(Review.rating),
                func.count(Review.id),
            ).where(Review.reviewee_instructor_id == instructor_id)
        )
        avg_rating, count = result.one()

        instructor = await self.db.execute(
            select(InstructorProfile).where(InstructorProfile.id == instructor_id)
        )
        instructor = instructor.scalar_one_or_none()
        if instructor:
            instructor.rating_average = Decimal(str(avg_rating or 0))
            instructor.review_count = count or 0

    async def _update_studio_rating(self, studio_id: UUID) -> None:
        result = await self.db.execute(
            select(
                func.avg(Review.rating),
                func.count(Review.id),
            ).where(Review.reviewee_studio_id == studio_id)
        )
        avg_rating, count = result.one()

        studio = await self.db.execute(
            select(StudioProfile).where(StudioProfile.id == studio_id)
        )
        studio = studio.scalar_one_or_none()
        if studio:
            studio.rating_average = Decimal(str(avg_rating or 0))
            studio.review_count = count or 0

    # -- Query helpers ---------------------------------------------------------

    async def get_user_review_for_application(
        self, application_id: UUID, user_id: UUID
    ) -> Optional[Review]:
        result = await self.db.execute(
            select(Review).where(
                Review.application_id == application_id,
                Review.reviewer_user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def get_both_reviewed(self, application_id: UUID) -> bool:
        if application_id is None:
            return False
        result = await self.db.execute(
            select(func.count(Review.id)).where(
                Review.application_id == application_id
            )
        )
        return (result.scalar() or 0) >= 2

    async def get_reviews_for_application(
        self, application_id: UUID
    ) -> List[Review]:
        result = await self.db.execute(
            select(Review)
            .where(Review.application_id == application_id)
            .order_by(Review.created_at.asc())
        )
        return list(result.scalars().all())

    async def get_reviews_for_instructor(
        self, instructor_id: UUID
    ) -> tuple[List[Review], Optional[float]]:
        result = await self.db.execute(
            select(Review)
            .where(Review.reviewee_instructor_id == instructor_id)
            .order_by(Review.created_at.desc())
        )
        reviews = list(result.scalars().all())

        avg_result = await self.db.execute(
            select(func.avg(Review.rating))
            .where(Review.reviewee_instructor_id == instructor_id)
        )
        avg_rating = avg_result.scalar()

        return reviews, float(avg_rating) if avg_rating else None

    async def get_reviews_for_studio(
        self, studio_id: UUID
    ) -> tuple[List[Review], Optional[float]]:
        result = await self.db.execute(
            select(Review)
            .where(Review.reviewee_studio_id == studio_id)
            .order_by(Review.created_at.desc())
        )
        reviews = list(result.scalars().all())

        avg_result = await self.db.execute(
            select(func.avg(Review.rating))
            .where(Review.reviewee_studio_id == studio_id)
        )
        avg_rating = avg_result.scalar()

        return reviews, float(avg_rating) if avg_rating else None

    # -- Update / Delete (unchanged, use review ID) ----------------------------

    async def update_review(
        self, review_id: UUID, user_id: UUID, data: ReviewUpdate
    ) -> Review:
        result = await self.db.execute(
            select(Review).where(Review.id == review_id)
        )
        review = result.scalar_one_or_none()

        if not review:
            raise ValueError("Review not found")

        if review.reviewer_user_id != user_id:
            raise PermissionError("Not authorized to update this review")

        if data.rating is not None:
            review.rating = data.rating
        if data.comment is not None:
            review.comment = data.comment
        if data.time_punctuality is not None:
            review.time_punctuality = data.time_punctuality
        if data.professionalism is not None:
            review.professionalism = data.professionalism
        if data.would_rehire is not None:
            review.would_rehire = data.would_rehire

        # Update average ratings
        if review.reviewee_instructor_id:
            await self._update_instructor_rating(review.reviewee_instructor_id)
        if review.reviewee_studio_id:
            await self._update_studio_rating(review.reviewee_studio_id)

        await self.db.commit()
        await self.db.refresh(review)
        return review

    async def delete_review(self, review_id: UUID, user_id: UUID) -> None:
        result = await self.db.execute(
            select(Review).where(Review.id == review_id)
        )
        review = result.scalar_one_or_none()

        if not review:
            raise ValueError("Review not found")

        if review.reviewer_user_id != user_id:
            raise PermissionError("Not authorized to delete this review")

        instructor_id = review.reviewee_instructor_id
        studio_id = review.reviewee_studio_id

        await self.db.delete(review)
        await self.db.commit()

        if instructor_id:
            await self._update_instructor_rating(instructor_id)
            await self.db.commit()
        if studio_id:
            await self._update_studio_rating(studio_id)
            await self.db.commit()
