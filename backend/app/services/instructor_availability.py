"""Instructor availability service -- standby pool management.

Instructors toggle themselves as "available now" and enter the dispatch pool.
The system uses their GPS coordinates and categories to match against urgent
job posts within a configurable radius.

Usage::

    service = InstructorAvailabilityService(db)
    record = await service.toggle_availability(user_id, True, lat=37.5, lng=127.0)
    nearby = await service.get_available_instructors(db, lat, lng, 5.0)
"""

import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

from sqlalchemy import select, update, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.instructor_availability import InstructorAvailability
from app.models.instructor import InstructorProfile
from app.models.user import User
from app.utils.distance import haversine_distance

logger = logging.getLogger(__name__)

# Default standby duration (hours) when toggling on
DEFAULT_AVAILABILITY_HOURS = 8


class InstructorAvailabilityService:
    """Manages the instructor standby pool for dispatch matching.

    Args:
        db: Async SQLAlchemy session.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def toggle_availability(
        self,
        user_id: str,
        is_available: bool,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        categories: Optional[list[str]] = None,
        max_distance_km: Optional[float] = None,
    ) -> InstructorAvailability:
        """Toggle instructor availability for dispatch matching.

        Args:
            user_id: The authenticated user's ID.
            is_available: Whether to enter (True) or leave (False) the pool.
            latitude: Current GPS latitude (required when toggling ON).
            longitude: Current GPS longitude (required when toggling ON).
            categories: List of categories the instructor can sub for.
            max_distance_km: Maximum travel distance preference in km.

        Returns:
            The upserted InstructorAvailability record.

        Raises:
            ValueError: If instructor profile not found, user is suspended,
                or GPS coordinates are missing when toggling on.
        """
        # Fetch instructor profile
        result = await self.db.execute(
            select(InstructorProfile).where(InstructorProfile.user_id == user_id)
        )
        instructor = result.scalar_one_or_none()
        if not instructor:
            raise ValueError("INSTRUCTOR_NOT_FOUND")

        # Check suspension status
        user_result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()
        if user and user.suspension_until and user.suspension_until > datetime.utcnow():
            raise PermissionError("USER_SUSPENDED")

        # Validate GPS when toggling on
        if is_available and (latitude is None or longitude is None):
            raise ValueError("GPS_REQUIRED")

        # Calculate available_until for on-toggle
        available_until: Optional[datetime] = None
        if is_available:
            available_until = datetime.utcnow() + timedelta(hours=DEFAULT_AVAILABILITY_HOURS)

        # Upsert: find existing record by user_id or create new
        existing_result = await self.db.execute(
            select(InstructorAvailability).where(
                InstructorAvailability.user_id == user_id
            )
        )
        record = existing_result.scalar_one_or_none()

        if record:
            # Update existing record
            record.is_available = is_available
            record.available_until = available_until
            if latitude is not None:
                record.latitude = Decimal(str(latitude))
            if longitude is not None:
                record.longitude = Decimal(str(longitude))
            if categories is not None:
                record.categories = categories
            if max_distance_km is not None:
                record.max_distance_km = Decimal(str(max_distance_km))
        else:
            # Create new record
            record = InstructorAvailability(
                instructor_id=instructor.id,
                user_id=user_id,
                is_available=is_available,
                available_until=available_until,
                latitude=Decimal(str(latitude)) if latitude is not None else None,
                longitude=Decimal(str(longitude)) if longitude is not None else None,
                categories=categories or [],
                max_distance_km=Decimal(str(max_distance_km)) if max_distance_km else Decimal("10.0"),
            )
            self.db.add(record)

        await self.db.flush()

        action = "on" if is_available else "off"
        logger.info(
            "Availability toggled %s: user=%s instructor=%s lat=%s lng=%s",
            action, user_id, instructor.id, latitude, longitude,
        )
        return record

    async def get_my_availability(
        self,
        user_id: str,
    ) -> Optional[InstructorAvailability]:
        """Get the current active availability record for the user.

        Returns None if no active availability exists or if it has expired.

        Args:
            user_id: The authenticated user's ID.

        Returns:
            The active InstructorAvailability record, or None.
        """
        now = datetime.utcnow()
        result = await self.db.execute(
            select(InstructorAvailability).where(
                and_(
                    InstructorAvailability.user_id == user_id,
                    InstructorAvailability.is_available.is_(True),
                    InstructorAvailability.available_until > now,
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_available_instructors(
        self,
        latitude: float,
        longitude: float,
        radius_km: float,
        category: Optional[str] = None,
    ) -> list[dict]:
        """Get available instructors within radius, sorted by distance.

        Uses a bounding-box pre-filter for performance, then applies
        precise haversine distance calculation as a post-filter.

        Args:
            latitude: Center point latitude (e.g., studio location).
            longitude: Center point longitude.
            radius_km: Search radius in kilometers.
            category: Optional category filter (e.g., "pilates", "yoga").

        Returns:
            List of dicts with availability record and computed distance,
            sorted by distance ascending. Each dict contains:
            - record: InstructorAvailability
            - distance_km: float
        """
        now = datetime.utcnow()

        # Bounding box pre-filter (rough, fast)
        # 1 degree latitude ~ 111 km
        # 1 degree longitude ~ 88 km at Seoul's latitude (~37.5N)
        lat_delta = radius_km / 111.0
        lng_delta = radius_km / 88.0

        min_lat = Decimal(str(latitude - lat_delta))
        max_lat = Decimal(str(latitude + lat_delta))
        min_lng = Decimal(str(longitude - lng_delta))
        max_lng = Decimal(str(longitude + lng_delta))

        stmt = select(InstructorAvailability).where(
            and_(
                InstructorAvailability.is_available.is_(True),
                InstructorAvailability.available_until > now,
                InstructorAvailability.latitude >= min_lat,
                InstructorAvailability.latitude <= max_lat,
                InstructorAvailability.longitude >= min_lng,
                InstructorAvailability.longitude <= max_lng,
            )
        )

        result = await self.db.execute(stmt)
        candidates = result.scalars().all()

        # Post-filter with precise haversine distance
        matched: list[dict] = []
        for record in candidates:
            if record.latitude is None or record.longitude is None:
                continue

            distance = haversine_distance(
                latitude, longitude,
                float(record.latitude), float(record.longitude),
            )

            if distance > radius_km:
                continue

            # Category filter: check if the instructor's categories JSON contains it
            if category and record.categories:
                if category not in record.categories:
                    continue
            elif category and not record.categories:
                continue

            matched.append({
                "record": record,
                "distance_km": round(distance, 2),
            })

        # Sort by distance ascending (nearest first)
        matched.sort(key=lambda x: x["distance_km"])

        logger.info(
            "Available instructors: %d found within %.1fkm of (%.4f, %.4f) category=%s",
            len(matched), radius_km, latitude, longitude, category,
        )
        return matched


async def expire_stale_availabilities(db: AsyncSession) -> int:
    """Expire all availability records past their available_until timestamp.

    Intended to be called periodically (e.g., every 5 minutes via scheduler).

    Args:
        db: Async SQLAlchemy session.

    Returns:
        Count of records expired.
    """
    now = datetime.utcnow()

    stmt = (
        update(InstructorAvailability)
        .where(
            and_(
                InstructorAvailability.is_available.is_(True),
                InstructorAvailability.available_until < now,
            )
        )
        .values(is_available=False)
    )

    result = await db.execute(stmt)
    expired_count: int = result.rowcount
    await db.flush()

    if expired_count > 0:
        logger.info("Expired %d stale availability records", expired_count)

    return expired_count
