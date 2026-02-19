from typing import Optional, List, Tuple
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.models import JobPost, StudioProfile, JobPostStatus
from app.schemas.job_post import JobPostCreate, JobPostUpdate, JobPostFilter


class JobPostService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_studio_profile_id(self, user_id: UUID) -> Optional[UUID]:
        result = await self.db.execute(
            select(StudioProfile.id).where(StudioProfile.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create(self, studio_id: UUID, data: JobPostCreate) -> JobPost:
        job_post = JobPost(
            studio_id=studio_id,
            **data.model_dump(),
        )
        self.db.add(job_post)
        await self.db.commit()
        await self.db.refresh(job_post)
        return job_post

    async def get_by_id(self, job_post_id: UUID) -> Optional[JobPost]:
        result = await self.db.execute(
            select(JobPost).where(JobPost.id == job_post_id)
        )
        return result.scalar_one_or_none()

    async def list(
        self,
        filters: JobPostFilter,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        premium_first: bool = True,  # v3.0: Premium priority sorting
    ) -> Tuple[List[JobPost], int]:
        from app.models import StudioProfile, User
        from sqlalchemy.orm import selectinload

        # Join with studio and user to get premium status
        query = (
            select(JobPost)
            .options(selectinload(JobPost.studio))
        )
        count_query = select(func.count(JobPost.id))

        # Apply filters
        conditions = []
        if filters.category:
            conditions.append(JobPost.category == filters.category)
        if filters.job_type:
            conditions.append(JobPost.job_type == filters.job_type)
        if filters.status:
            conditions.append(JobPost.status == filters.status)
        else:
            # Default to open jobs only
            conditions.append(JobPost.status == JobPostStatus.OPEN)
        if filters.region:
            conditions.append(JobPost.region == filters.region)
        if filters.date_from:
            conditions.append(JobPost.date >= filters.date_from)
        if filters.date_to:
            conditions.append(JobPost.date <= filters.date_to)
        if filters.min_rate:
            conditions.append(JobPost.hourly_rate >= filters.min_rate)
        if filters.max_rate:
            conditions.append(JobPost.hourly_rate <= filters.max_rate)

        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))

        # Get total count
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        # Apply sorting with premium priority (v3.0)
        if premium_first:
            # Join with user table to get premium status
            query = query.join(StudioProfile, JobPost.studio_id == StudioProfile.id)
            query = query.join(User, StudioProfile.user_id == User.id)

            # Sort by premium status first, then by the requested column
            sort_column = getattr(JobPost, sort_by, JobPost.created_at)
            if sort_order == "desc":
                query = query.order_by(
                    User.membership_tier.desc(),  # Premium first
                    sort_column.desc()
                )
            else:
                query = query.order_by(
                    User.membership_tier.desc(),  # Premium first
                    sort_column.asc()
                )
        else:
            # Standard sorting without premium priority
            sort_column = getattr(JobPost, sort_by, JobPost.created_at)
            if sort_order == "desc":
                query = query.order_by(sort_column.desc())
            else:
                query = query.order_by(sort_column.asc())

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await self.db.execute(query)
        items = result.scalars().all()

        return list(items), total

    async def update(
        self, job_post_id: UUID, studio_id: UUID, data: JobPostUpdate
    ) -> Optional[JobPost]:
        job_post = await self.get_by_id(job_post_id)
        if not job_post:
            return None
        if job_post.studio_id != studio_id:
            raise PermissionError("Not authorized to update this job post")

        update_dict = data.model_dump(exclude_unset=True)
        for field, value in update_dict.items():
            setattr(job_post, field, value)

        await self.db.commit()
        await self.db.refresh(job_post)
        return job_post

    async def delete(self, job_post_id: UUID, studio_id: UUID) -> bool:
        job_post = await self.get_by_id(job_post_id)
        if not job_post:
            return False
        if job_post.studio_id != studio_id:
            raise PermissionError("Not authorized to delete this job post")

        await self.db.delete(job_post)
        await self.db.commit()
        return True

    async def get_by_studio(
        self, studio_id: UUID, page: int = 1, page_size: int = 20
    ) -> Tuple[List[JobPost], int]:
        query = select(JobPost).where(JobPost.studio_id == studio_id)
        count_query = select(func.count(JobPost.id)).where(JobPost.studio_id == studio_id)

        total_result = await self.db.execute(count_query)
        total = total_result.scalar()

        query = query.order_by(JobPost.created_at.desc())
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await self.db.execute(query)
        items = result.scalars().all()

        return list(items), total
