from typing import Optional, List
from uuid import UUID
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_

from app.models import (
    Offer, Application, InstructorProfile, StudioProfile,
    OfferStatus, ApplicationStatus
)
from app.schemas.offer import OfferCreate


class OfferService:
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

    async def get_by_id(self, offer_id: UUID) -> Optional[Offer]:
        result = await self.db.execute(
            select(Offer).where(Offer.id == offer_id)
        )
        return result.scalar_one_or_none()

    async def create(self, studio_id: UUID, data: OfferCreate) -> Offer:
        instructor_id = None

        if data.application_id:
            # Application-based offer
            application = await self.db.execute(
                select(Application).where(Application.id == data.application_id)
            )
            application = application.scalar_one_or_none()

            if not application:
                raise ValueError("Application not found")

            if application.status != ApplicationStatus.PENDING:
                raise ValueError("Application is not pending")

            # Check if offer already exists for this application
            existing = await self.db.execute(
                select(Offer).where(Offer.application_id == data.application_id)
            )
            if existing.scalar_one_or_none():
                raise ValueError("Offer already exists for this application")

            instructor_id = application.instructor_id
            # Application status remains PENDING until instructor accepts/rejects offer
        elif data.instructor_id:
            # Direct offer
            instructor = await self.db.execute(
                select(InstructorProfile).where(InstructorProfile.id == data.instructor_id)
            )
            if not instructor.scalar_one_or_none():
                raise ValueError("Instructor not found")
            instructor_id = data.instructor_id
        else:
            raise ValueError("Either application_id or instructor_id is required")

        # Create offer with 7-day expiration
        offer = Offer(
            application_id=data.application_id,
            studio_id=studio_id,
            instructor_id=instructor_id,
            status=OfferStatus.PENDING,
            message=data.message,
            proposed_rate=data.proposed_rate,
            expires_at=datetime.utcnow() + timedelta(days=7),
        )
        self.db.add(offer)
        await self.db.commit()
        await self.db.refresh(offer)

        # Send notification to instructor
        try:
            from app.services.notification import notify_offer_received
            instructor_profile = await self.db.execute(
                select(InstructorProfile).where(InstructorProfile.id == instructor_id)
            )
            inst = instructor_profile.scalar_one_or_none()
            studio_profile = await self.db.execute(
                select(StudioProfile).where(StudioProfile.id == studio_id)
            )
            studio = studio_profile.scalar_one_or_none()
            if inst and studio:
                await notify_offer_received(
                    self.db,
                    str(inst.user_id),
                    studio.business_name or "스튜디오",
                )
        except Exception:
            pass  # Notification failure should not block the offer

        return offer

    async def get_by_user(self, user_id: UUID, role: str) -> List[Offer]:
        if role == "instructor":
            instructor_id = await self.get_instructor_profile_id(user_id)
            if not instructor_id:
                return []
            result = await self.db.execute(
                select(Offer)
                .where(Offer.instructor_id == instructor_id)
                .order_by(Offer.created_at.desc())
            )
        else:
            studio_id = await self.get_studio_profile_id(user_id)
            if not studio_id:
                return []
            result = await self.db.execute(
                select(Offer)
                .where(Offer.studio_id == studio_id)
                .order_by(Offer.created_at.desc())
            )

        return list(result.scalars().all())

    async def accept(self, offer_id: UUID, instructor_id: UUID) -> Offer:
        offer = await self.get_by_id(offer_id)

        if not offer:
            raise ValueError("Offer not found")

        if offer.instructor_id != instructor_id:
            raise PermissionError("Not authorized to accept this offer")

        if offer.status != OfferStatus.PENDING:
            raise ValueError("OFFER_NOT_PENDING")

        if offer.expires_at and offer.expires_at < datetime.utcnow():
            offer.status = OfferStatus.EXPIRED
            await self.db.commit()
            raise ValueError("Offer has expired")

        offer.status = OfferStatus.ACCEPTED

        # Update application status if this offer was from an application
        if offer.application_id:
            application = await self.db.execute(
                select(Application).where(Application.id == offer.application_id)
            )
            application = application.scalar_one_or_none()
            if application:
                application.status = ApplicationStatus.ACCEPTED

        await self.db.commit()
        await self.db.refresh(offer)
        return offer

    async def reject(self, offer_id: UUID, instructor_id: UUID) -> Offer:
        offer = await self.get_by_id(offer_id)

        if not offer:
            raise ValueError("Offer not found")

        if offer.instructor_id != instructor_id:
            raise PermissionError("Not authorized to reject this offer")

        if offer.status != OfferStatus.PENDING:
            raise ValueError("OFFER_NOT_PENDING")

        offer.status = OfferStatus.REJECTED

        # Update application status if this offer was from an application
        if offer.application_id:
            application = await self.db.execute(
                select(Application).where(Application.id == offer.application_id)
            )
            application = application.scalar_one_or_none()
            if application:
                application.status = ApplicationStatus.REJECTED

        await self.db.commit()
        await self.db.refresh(offer)
        return offer
