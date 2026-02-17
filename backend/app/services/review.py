from typing import Optional, List
from uuid import UUID
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update, delete

from app.models import (
    Review, Contract, InstructorProfile, StudioProfile,
    ContractStatus, UserRole
)
from app.schemas.review import ReviewCreate, ReviewUpdate


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

    async def get_user_review_for_contract(
        self, contract_id: UUID, user_id: UUID
    ) -> Optional[Review]:
        """Get a specific user's review for a contract."""
        result = await self.db.execute(
            select(Review).where(
                Review.contract_id == contract_id,
                Review.reviewer_user_id == user_id
            )
        )
        return result.scalar_one_or_none()

    async def update_review(
        self, review_id: UUID, user_id: UUID, data: ReviewUpdate
    ) -> Review:
        """Update an existing review."""
        # Get the review
        result = await self.db.execute(
            select(Review).where(Review.id == review_id)
        )
        review = result.scalar_one_or_none()

        if not review:
            raise ValueError("Review not found")

        if review.reviewer_user_id != user_id:
            raise PermissionError("Not authorized to update this review")

        # Update fields
        if data.rating is not None:
            review.rating = data.rating
        if data.comment is not None:
            review.comment = data.comment

        # Update average ratings
        if review.reviewee_instructor_id:
            await self._update_instructor_rating(review.reviewee_instructor_id)
        if review.reviewee_studio_id:
            await self._update_studio_rating(review.reviewee_studio_id)

        await self.db.commit()
        await self.db.refresh(review)
        return review

    async def delete_review(self, review_id: UUID, user_id: UUID) -> None:
        """Delete a review."""
        # Get the review
        result = await self.db.execute(
            select(Review).where(Review.id == review_id)
        )
        review = result.scalar_one_or_none()

        if not review:
            raise ValueError("Review not found")

        if review.reviewer_user_id != user_id:
            raise PermissionError("Not authorized to delete this review")

        # Store IDs before deletion for rating update
        instructor_id = review.reviewee_instructor_id
        studio_id = review.reviewee_studio_id

        # Delete the review
        await self.db.delete(review)
        await self.db.commit()

        # Update average ratings
        if instructor_id:
            await self._update_instructor_rating(instructor_id)
            await self.db.commit()
        if studio_id:
            await self._update_studio_rating(studio_id)
            await self.db.commit()
