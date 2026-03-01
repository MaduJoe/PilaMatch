"""Service for recording and querying generic domain events.

Usage::

    service = EventLogService(db)
    await service.log(
        event_type="contract.status_changed",
        actor_user_id="...",
        target_type="contract",
        target_id="...",
        data={"from_status": "confirmed", "to_status": "in_progress"},
    )

All public methods are designed to *never* raise exceptions that could
disrupt the caller's main business logic -- errors are caught and logged.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.event_log import EventLog

logger = logging.getLogger(__name__)


class EventLogService:
    """Thin wrapper around the ``event_logs`` table.

    Args:
        db: Async SQLAlchemy session.
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def log(
        self,
        event_type: str,
        actor_user_id: Optional[str] = None,
        target_type: Optional[str] = None,
        target_id: Optional[str] = None,
        data: Optional[Dict[str, Any]] = None,
        note: Optional[str] = None,
    ) -> Optional[EventLog]:
        """Persist a single event log entry.

        Args:
            event_type: Dot-notation event name (e.g. ``"contract.status_changed"``).
            actor_user_id: UUID string of the user who triggered the event.
            target_type: Entity type affected (e.g. ``"contract"``).
            target_id: UUID string of the affected entity.
            data: Free-form JSON metadata.
            note: Human-readable description.

        Returns:
            The created ``EventLog`` instance, or ``None`` if persistence
            failed (the error is logged but not re-raised).
        """
        try:
            event = EventLog(
                event_type=event_type,
                actor_user_id=actor_user_id,
                target_type=target_type,
                target_id=target_id,
                data=data or {},
                note=note,
            )
            self.db.add(event)
            await self.db.flush()
            logger.info(
                "Event logged: type=%s target=%s/%s actor=%s",
                event_type,
                target_type,
                target_id,
                actor_user_id,
            )
            return event
        except Exception:
            # Rollback to clear the failed flush and restore a usable session.
            # Without this, subsequent operations on the same session would fail
            # with "Can't reconnect until invalid transaction is rolled back".
            await self.db.rollback()
            logger.exception(
                "Failed to log event: type=%s target=%s/%s",
                event_type,
                target_type,
                target_id,
            )
            return None

    async def get_events(
        self,
        target_type: Optional[str] = None,
        target_id: Optional[str] = None,
        event_type: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[EventLog], int]:
        """Query events with optional filters.

        Args:
            target_type: Filter by target entity type.
            target_id: Filter by target entity id.
            event_type: Filter by event type.
            skip: Number of records to skip (pagination offset).
            limit: Maximum number of records to return.

        Returns:
            A tuple of ``(events, total_count)``.
        """
        filters = []
        if target_type is not None:
            filters.append(EventLog.target_type == target_type)
        if target_id is not None:
            filters.append(EventLog.target_id == target_id)
        if event_type is not None:
            filters.append(EventLog.event_type == event_type)

        # Total count
        count_stmt = select(func.count(EventLog.id)).where(*filters)
        total = (await self.db.execute(count_stmt)).scalar_one()

        # Fetch page
        query = (
            select(EventLog)
            .where(*filters)
            .order_by(EventLog.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        events = list(result.scalars().all())

        return events, total

    async def get_user_events(
        self,
        user_id: str,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[EventLog], int]:
        """Return all events triggered by a specific user.

        Args:
            user_id: UUID string of the actor.
            skip: Pagination offset.
            limit: Page size.

        Returns:
            A tuple of ``(events, total_count)``.
        """
        filters = [EventLog.actor_user_id == user_id]

        count_stmt = select(func.count(EventLog.id)).where(*filters)
        total = (await self.db.execute(count_stmt)).scalar_one()

        query = (
            select(EventLog)
            .where(*filters)
            .order_by(EventLog.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await self.db.execute(query)
        events = list(result.scalars().all())

        return events, total
