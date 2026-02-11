from typing import Optional, List
from uuid import UUID
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models import (
    Review, Contract, InstructorProfile, StudioProfile,
    ContractStatus, UserRole
)
from app.schemas.review import ReviewCreate


class ReviewService:
    def __init__(self, db: AsyncSession):
        self.db = db

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

    async def create_review(
        self,
        contract_id: UUID,
        reviewer_user_id: UUID,
        reviewer_role: str,
        data: ReviewCreate,
    ) -> Review:
        # Get contract
        contract = await self.db.execute(
            select(Contract).where(Contract.id == contract_id)
        )
        contract = contract.scalar_one_or_none()

        if not contract:
            raise ValueError("Contract not found")

        if contract.status != ContractStatus.COMPLETED:
            raise ValueError("Can only review completed contracts")

        # Check if user is part of contract
        if reviewer_role == "studio":
            studio_id = await self.get_studio_profile_id(reviewer_user_id)
            if contract.studio_id != studio_id:
                raise PermissionError("Not authorized to review this contract")
            reviewee_instructor_id = contract.instructor_id
            reviewee_studio_id = None
        else:
            instructor_id = await self.get_instructor_profile_id(reviewer_user_id)
            if contract.instructor_id != instructor_id:
                raise PermissionError("Not authorized to review this contract")
            reviewee_instructor_id = None
            reviewee_studio_id = contract.studio_id

        # Check for duplicate review
        existing = await self.db.execute(
            select(Review).where(
                Review.contract_id == contract_id,
                Review.reviewer_user_id == reviewer_user_id,
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError("Review already exists for this contract")

        # Create review
        review = Review(
            contract_id=contract_id,
            reviewer_user_id=reviewer_user_id,
            reviewee_instructor_id=reviewee_instructor_id,
            reviewee_studio_id=reviewee_studio_id,
            rating=data.rating,
            comment=data.comment,
        )
        self.db.add(review)

        # Update average rating
        if reviewee_instructor_id:
            await self._update_instructor_rating(reviewee_instructor_id)
        if reviewee_studio_id:
            await self._update_studio_rating(reviewee_studio_id)

        await self.db.commit()
        await self.db.refresh(review)
        return review

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
