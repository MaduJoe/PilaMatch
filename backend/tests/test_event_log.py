"""Unit tests for the generic EventLog model and EventLogService.

Tests cover:
1. EventLog model creation with all fields
2. EventLogService.log() -- successful persistence
3. EventLogService.log() -- failure is silently caught (no exception leaks)
4. EventLogService.get_events() -- filter by target_type, target_id, event_type
5. EventLogService.get_user_events() -- filter by actor_user_id
6. Pagination (skip / limit) behaviour
"""

import os
import uuid
from datetime import datetime
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.db.session import Base
from app.models.event_log import EventLog
from app.services.event_log import EventLogService


# ---------------------------------------------------------------------------
# Fixtures: in-memory SQLite async session
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def async_session() -> AsyncGenerator[AsyncSession, None]:
    """Create an in-memory SQLite database with the event_logs table."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    session_factory = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with session_factory() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


# ---------------------------------------------------------------------------
# 1. Model creation
# ---------------------------------------------------------------------------

class TestEventLogModel:
    """Verify that EventLog records can be created and persisted."""

    @pytest.mark.asyncio
    async def test_create_event_log_with_all_fields(
        self, async_session: AsyncSession
    ) -> None:
        """EventLog row with every field populated is round-tripped correctly."""
        actor_id = uuid.uuid4()
        target_id = str(uuid.uuid4())

        event = EventLog(
            event_type="contract.status_changed",
            actor_user_id=actor_id,
            target_type="contract",
            target_id=target_id,
            data={"from_status": "confirmed", "to_status": "in_progress"},
            note="Both parties signed",
        )
        async_session.add(event)
        await async_session.commit()
        await async_session.refresh(event)

        assert event.id is not None
        assert event.event_type == "contract.status_changed"
        assert str(event.actor_user_id) == str(actor_id)
        assert event.target_type == "contract"
        assert event.target_id == target_id
        assert event.data["from_status"] == "confirmed"
        assert event.note == "Both parties signed"
        assert isinstance(event.created_at, datetime)
        assert isinstance(event.updated_at, datetime)

    @pytest.mark.asyncio
    async def test_create_event_log_minimal(
        self, async_session: AsyncSession
    ) -> None:
        """EventLog with only required fields (event_type) persists."""
        event = EventLog(event_type="user.registered")
        async_session.add(event)
        await async_session.commit()
        await async_session.refresh(event)

        assert event.id is not None
        assert event.event_type == "user.registered"
        assert event.actor_user_id is None
        assert event.target_type is None
        assert event.target_id is None


# ---------------------------------------------------------------------------
# 2. EventLogService.log()
# ---------------------------------------------------------------------------

class TestEventLogServiceLog:
    """Verify the log() method."""

    @pytest.mark.asyncio
    async def test_log_creates_event(self, async_session: AsyncSession) -> None:
        """log() inserts a row and returns the EventLog instance."""
        service = EventLogService(async_session)
        actor_id = str(uuid.uuid4())
        target_id = str(uuid.uuid4())

        result = await service.log(
            event_type="application.submitted",
            actor_user_id=actor_id,
            target_type="job_post",
            target_id=target_id,
            data={"application_id": str(uuid.uuid4())},
            note="Instructor applied",
        )
        await async_session.commit()

        assert result is not None
        assert result.event_type == "application.submitted"
        assert str(result.actor_user_id) == actor_id
        assert result.target_type == "job_post"

        # Verify persisted
        rows = (
            await async_session.execute(
                select(EventLog).where(EventLog.event_type == "application.submitted")
            )
        ).scalars().all()
        assert len(rows) == 1

    @pytest.mark.asyncio
    async def test_log_failure_returns_none(
        self, async_session: AsyncSession
    ) -> None:
        """If the DB operation fails, log() returns None instead of raising."""
        service = EventLogService(async_session)

        # Patch flush to simulate a DB error
        with patch.object(async_session, "flush", side_effect=Exception("DB error")):
            result = await service.log(event_type="boom.error")

        assert result is None

    @pytest.mark.asyncio
    async def test_log_with_none_data_defaults_to_empty_dict(
        self, async_session: AsyncSession
    ) -> None:
        """When data is None, the stored value should be an empty dict."""
        service = EventLogService(async_session)
        result = await service.log(event_type="test.default_data", data=None)
        await async_session.commit()

        assert result is not None
        assert result.data == {}


# ---------------------------------------------------------------------------
# 3. EventLogService.get_events() -- filtering
# ---------------------------------------------------------------------------

class TestEventLogServiceGetEvents:
    """Verify get_events() with various filters."""

    async def _seed_events(self, session: AsyncSession) -> None:
        """Insert a handful of events for query tests."""
        service = EventLogService(session)
        user_a = str(uuid.uuid4())
        user_b = str(uuid.uuid4())
        contract_1 = str(uuid.uuid4())
        contract_2 = str(uuid.uuid4())
        job_post_1 = str(uuid.uuid4())

        await service.log("contract.status_changed", user_a, "contract", contract_1, {"to": "in_progress"})
        await service.log("contract.status_changed", user_a, "contract", contract_2, {"to": "completed"})
        await service.log("application.submitted", user_b, "job_post", job_post_1)
        await service.log("dispute.no_show_reported", user_a, "contract", contract_1, {"count": 1})
        await service.log("user.verified", user_b, "user", str(user_b))
        await session.commit()

        # Store IDs for assertions
        self._user_a = user_a
        self._user_b = user_b
        self._contract_1 = contract_1

    @pytest.mark.asyncio
    async def test_get_all_events(self, async_session: AsyncSession) -> None:
        """No filters returns all events."""
        await self._seed_events(async_session)
        service = EventLogService(async_session)

        events, total = await service.get_events()
        assert total == 5
        assert len(events) == 5

    @pytest.mark.asyncio
    async def test_filter_by_target_type(self, async_session: AsyncSession) -> None:
        await self._seed_events(async_session)
        service = EventLogService(async_session)

        events, total = await service.get_events(target_type="contract")
        assert total == 3  # 2 status_changed + 1 no_show_reported

    @pytest.mark.asyncio
    async def test_filter_by_target_id(self, async_session: AsyncSession) -> None:
        await self._seed_events(async_session)
        service = EventLogService(async_session)

        events, total = await service.get_events(
            target_type="contract", target_id=self._contract_1
        )
        assert total == 2  # status_changed + no_show_reported on contract_1

    @pytest.mark.asyncio
    async def test_filter_by_event_type(self, async_session: AsyncSession) -> None:
        await self._seed_events(async_session)
        service = EventLogService(async_session)

        events, total = await service.get_events(event_type="application.submitted")
        assert total == 1
        assert events[0].event_type == "application.submitted"

    @pytest.mark.asyncio
    async def test_pagination_skip_limit(self, async_session: AsyncSession) -> None:
        """skip and limit correctly paginate results."""
        await self._seed_events(async_session)
        service = EventLogService(async_session)

        events_page1, total = await service.get_events(skip=0, limit=2)
        assert total == 5
        assert len(events_page1) == 2

        events_page2, _ = await service.get_events(skip=2, limit=2)
        assert len(events_page2) == 2

        events_page3, _ = await service.get_events(skip=4, limit=2)
        assert len(events_page3) == 1

        # No overlap
        all_ids = {e.id for e in events_page1} | {e.id for e in events_page2} | {e.id for e in events_page3}
        assert len(all_ids) == 5


# ---------------------------------------------------------------------------
# 4. EventLogService.get_user_events()
# ---------------------------------------------------------------------------

class TestEventLogServiceGetUserEvents:
    """Verify get_user_events() returns only events by a given actor."""

    @pytest.mark.asyncio
    async def test_returns_only_actor_events(
        self, async_session: AsyncSession
    ) -> None:
        service = EventLogService(async_session)
        user_a = str(uuid.uuid4())
        user_b = str(uuid.uuid4())

        await service.log("action.one", actor_user_id=user_a, target_type="x", target_id="1")
        await service.log("action.two", actor_user_id=user_a, target_type="x", target_id="2")
        await service.log("action.three", actor_user_id=user_b, target_type="x", target_id="3")
        await async_session.commit()

        events, total = await service.get_user_events(user_a)
        assert total == 2
        assert len(events) == 2
        assert all(str(e.actor_user_id) == user_a for e in events)

    @pytest.mark.asyncio
    async def test_pagination(self, async_session: AsyncSession) -> None:
        service = EventLogService(async_session)
        user_id = str(uuid.uuid4())

        for i in range(7):
            await service.log(f"action.{i}", actor_user_id=user_id)
        await async_session.commit()

        page1, total = await service.get_user_events(user_id, skip=0, limit=3)
        assert total == 7
        assert len(page1) == 3

        page2, _ = await service.get_user_events(user_id, skip=3, limit=3)
        assert len(page2) == 3

        page3, _ = await service.get_user_events(user_id, skip=6, limit=3)
        assert len(page3) == 1

    @pytest.mark.asyncio
    async def test_no_events_for_user(self, async_session: AsyncSession) -> None:
        service = EventLogService(async_session)
        events, total = await service.get_user_events(str(uuid.uuid4()))
        assert total == 0
        assert events == []
