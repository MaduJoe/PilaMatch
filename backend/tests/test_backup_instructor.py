"""Unit tests for Phase 3: Backup Instructor Network.

Covers:
1. BackupInstructor model column existence and constraints
2. BackupInstructorService CRUD operations (add, list, update, delete)
3. BackupInstructorService edge cases (duplicate, not found)
4. Pydantic schemas (create, update, response)
5. Router registration
"""

import uuid
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas.backup_instructor import (
    BackupInstructorCreate,
    BackupInstructorUpdate,
    BackupInstructorResponse,
    BackupInstructorListResponse,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_backup_instructor(
    studio_id: uuid.UUID = None,
    instructor_id: uuid.UUID = None,
    nickname: str = "Kim Coach",
    note: str = "Very reliable",
    priority: int = 1,
    total_completed: int = 5,
) -> MagicMock:
    """Create a fake BackupInstructor model instance."""
    backup = MagicMock()
    backup.id = uuid.uuid4()
    backup.studio_id = studio_id or uuid.uuid4()
    backup.instructor_id = instructor_id or uuid.uuid4()
    backup.nickname = nickname
    backup.note = note
    backup.priority = priority
    backup.last_worked_at = None
    backup.total_completed = total_completed
    backup.created_at = datetime.utcnow()
    backup.updated_at = datetime.utcnow()
    return backup


def _make_instructor_profile(
    profile_id: uuid.UUID = None,
    display_name: str = "Test Instructor",
    phone: str = "010-1234-5678",
    categories: list = None,
    rating_average=None,
) -> MagicMock:
    """Create a fake InstructorProfile model instance."""
    profile = MagicMock()
    profile.id = profile_id or uuid.uuid4()
    profile.display_name = display_name
    profile.phone = phone
    profile.categories = categories or ["pilates"]
    profile.rating_average = rating_average
    return profile


# ===========================================================================
# 1. Model column existence
# ===========================================================================

class TestBackupInstructorModel:
    """Tests for the BackupInstructor model definition."""

    def test_model_exists(self) -> None:
        """BackupInstructor model should be importable."""
        from app.models.backup_instructor import BackupInstructor
        assert BackupInstructor.__tablename__ == "backup_instructors"

    def test_model_has_required_columns(self) -> None:
        """BackupInstructor should have all expected columns."""
        from app.models.backup_instructor import BackupInstructor

        columns = BackupInstructor.__table__.columns
        expected = [
            "id", "studio_id", "instructor_id", "nickname",
            "note", "priority", "last_worked_at", "total_completed",
            "created_at", "updated_at",
        ]
        for col_name in expected:
            assert col_name in columns, f"Missing column: {col_name}"

    def test_model_unique_constraint(self) -> None:
        """BackupInstructor should have unique constraint on (studio_id, instructor_id)."""
        from app.models.backup_instructor import BackupInstructor

        constraints = BackupInstructor.__table__.constraints
        unique_names = [
            c.name for c in constraints
            if hasattr(c, 'name') and c.name
        ]
        assert "uq_backup_studio_instructor" in unique_names

    def test_model_in_init(self) -> None:
        """BackupInstructor should be exported from models/__init__.py."""
        from app.models import BackupInstructor
        assert BackupInstructor.__tablename__ == "backup_instructors"

    def test_studio_id_is_indexed(self) -> None:
        """studio_id should be indexed for efficient queries."""
        from app.models.backup_instructor import BackupInstructor

        col = BackupInstructor.__table__.columns["studio_id"]
        assert col.index is True

    def test_instructor_id_is_indexed(self) -> None:
        """instructor_id should be indexed for efficient queries."""
        from app.models.backup_instructor import BackupInstructor

        col = BackupInstructor.__table__.columns["instructor_id"]
        assert col.index is True

    def test_priority_default_is_3(self) -> None:
        """priority should default to 3."""
        from app.models.backup_instructor import BackupInstructor

        col = BackupInstructor.__table__.columns["priority"]
        assert col.default is not None
        assert col.default.arg == 3


# ===========================================================================
# 2. BackupInstructorService — add
# ===========================================================================

class TestBackupInstructorServiceAdd:
    """Tests for BackupInstructorService.add method."""

    @pytest.mark.asyncio
    async def test_add_success(self) -> None:
        """Adding a valid instructor to backup should succeed."""
        from app.services.backup_instructor import BackupInstructorService

        mock_db = AsyncMock()

        # Instructor exists
        mock_instructor_result = MagicMock()
        mock_instructor_result.scalar_one_or_none.return_value = _make_instructor_profile()

        # No duplicate
        mock_duplicate_result = MagicMock()
        mock_duplicate_result.scalar_one_or_none.return_value = None

        mock_db.execute.side_effect = [mock_instructor_result, mock_duplicate_result]

        service = BackupInstructorService(mock_db)
        data = BackupInstructorCreate(
            instructor_id=uuid.uuid4(),
            nickname="Kim Coach",
            priority=1,
        )

        studio_id = uuid.uuid4()
        result = await service.add(studio_id, data)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_instructor_not_found(self) -> None:
        """Adding a non-existent instructor should raise INSTRUCTOR_NOT_FOUND."""
        from app.services.backup_instructor import BackupInstructorService

        mock_db = AsyncMock()

        mock_instructor_result = MagicMock()
        mock_instructor_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_instructor_result

        service = BackupInstructorService(mock_db)
        data = BackupInstructorCreate(instructor_id=uuid.uuid4())

        with pytest.raises(ValueError, match="INSTRUCTOR_NOT_FOUND"):
            await service.add(uuid.uuid4(), data)

    @pytest.mark.asyncio
    async def test_add_duplicate_raises_error(self) -> None:
        """Adding an instructor already in the backup should raise ALREADY_IN_BACKUP."""
        from app.services.backup_instructor import BackupInstructorService

        mock_db = AsyncMock()

        # Instructor exists
        mock_instructor_result = MagicMock()
        mock_instructor_result.scalar_one_or_none.return_value = _make_instructor_profile()

        # Already in backup
        mock_duplicate_result = MagicMock()
        mock_duplicate_result.scalar_one_or_none.return_value = _make_backup_instructor()

        mock_db.execute.side_effect = [mock_instructor_result, mock_duplicate_result]

        service = BackupInstructorService(mock_db)
        data = BackupInstructorCreate(instructor_id=uuid.uuid4())

        with pytest.raises(ValueError, match="ALREADY_IN_BACKUP"):
            await service.add(uuid.uuid4(), data)


# ===========================================================================
# 3. BackupInstructorService — list
# ===========================================================================

class TestBackupInstructorServiceList:
    """Tests for BackupInstructorService.list_by_studio method."""

    @pytest.mark.asyncio
    async def test_list_returns_tuples(self) -> None:
        """list_by_studio should return (BackupInstructor, InstructorProfile) tuples."""
        from app.services.backup_instructor import BackupInstructorService

        mock_db = AsyncMock()
        backup = _make_backup_instructor()
        instructor = _make_instructor_profile()

        mock_result = MagicMock()
        mock_result.all.return_value = [(backup, instructor)]
        mock_db.execute.return_value = mock_result

        service = BackupInstructorService(mock_db)
        results = await service.list_by_studio(uuid.uuid4())

        assert len(results) == 1
        assert results[0] == (backup, instructor)

    @pytest.mark.asyncio
    async def test_list_empty_studio(self) -> None:
        """list_by_studio should return empty list for a studio with no backups."""
        from app.services.backup_instructor import BackupInstructorService

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_db.execute.return_value = mock_result

        service = BackupInstructorService(mock_db)
        results = await service.list_by_studio(uuid.uuid4())

        assert results == []


# ===========================================================================
# 4. BackupInstructorService — update
# ===========================================================================

class TestBackupInstructorServiceUpdate:
    """Tests for BackupInstructorService.update method."""

    @pytest.mark.asyncio
    async def test_update_success(self) -> None:
        """Updating an existing backup entry should succeed."""
        from app.services.backup_instructor import BackupInstructorService

        mock_db = AsyncMock()
        backup = _make_backup_instructor(priority=3)

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = backup
        mock_db.execute.return_value = mock_result

        service = BackupInstructorService(mock_db)
        data = BackupInstructorUpdate(priority=1, nickname="Updated Nick")

        result = await service.update(uuid.uuid4(), uuid.uuid4(), data)

        assert result is not None
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_not_found_returns_none(self) -> None:
        """Updating a non-existent entry should return None."""
        from app.services.backup_instructor import BackupInstructorService

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        service = BackupInstructorService(mock_db)
        data = BackupInstructorUpdate(priority=2)

        result = await service.update(uuid.uuid4(), uuid.uuid4(), data)

        assert result is None
        mock_db.commit.assert_not_called()


# ===========================================================================
# 5. BackupInstructorService — delete
# ===========================================================================

class TestBackupInstructorServiceDelete:
    """Tests for BackupInstructorService.delete method."""

    @pytest.mark.asyncio
    async def test_delete_success(self) -> None:
        """Deleting an existing backup entry should return True."""
        from app.services.backup_instructor import BackupInstructorService

        mock_db = AsyncMock()
        backup = _make_backup_instructor()

        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = backup
        mock_db.execute.return_value = mock_result

        service = BackupInstructorService(mock_db)
        result = await service.delete(uuid.uuid4(), uuid.uuid4())

        assert result is True
        mock_db.delete.assert_called_once_with(backup)
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_not_found_returns_false(self) -> None:
        """Deleting a non-existent entry should return False."""
        from app.services.backup_instructor import BackupInstructorService

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        service = BackupInstructorService(mock_db)
        result = await service.delete(uuid.uuid4(), uuid.uuid4())

        assert result is False
        mock_db.delete.assert_not_called()


# ===========================================================================
# 6. BackupInstructorService — get_backup_instructor_ids
# ===========================================================================

class TestBackupInstructorServiceGetIds:
    """Tests for BackupInstructorService.get_backup_instructor_ids."""

    @pytest.mark.asyncio
    async def test_returns_ordered_ids(self) -> None:
        """Should return instructor IDs ordered by priority."""
        from app.services.backup_instructor import BackupInstructorService

        mock_db = AsyncMock()
        id1 = uuid.uuid4()
        id2 = uuid.uuid4()

        mock_result = MagicMock()
        mock_result.all.return_value = [(id1,), (id2,)]
        mock_db.execute.return_value = mock_result

        service = BackupInstructorService(mock_db)
        ids = await service.get_backup_instructor_ids(uuid.uuid4())

        assert ids == [id1, id2]

    @pytest.mark.asyncio
    async def test_returns_empty_for_no_backups(self) -> None:
        """Should return empty list if studio has no backups."""
        from app.services.backup_instructor import BackupInstructorService

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.all.return_value = []
        mock_db.execute.return_value = mock_result

        service = BackupInstructorService(mock_db)
        ids = await service.get_backup_instructor_ids(uuid.uuid4())

        assert ids == []


# ===========================================================================
# 7. Schema validation
# ===========================================================================

class TestBackupInstructorSchemas:
    """Tests for Pydantic schemas."""

    def test_create_schema_valid(self) -> None:
        """BackupInstructorCreate should accept valid input."""
        schema = BackupInstructorCreate(
            instructor_id=uuid.uuid4(),
            nickname="Kim Coach",
            note="Great substitute",
            priority=1,
        )
        assert schema.priority == 1
        assert schema.nickname == "Kim Coach"

    def test_create_schema_priority_defaults_to_3(self) -> None:
        """priority should default to 3."""
        schema = BackupInstructorCreate(instructor_id=uuid.uuid4())
        assert schema.priority == 3

    def test_create_schema_priority_validation(self) -> None:
        """priority must be between 1 and 3."""
        with pytest.raises(Exception):
            BackupInstructorCreate(instructor_id=uuid.uuid4(), priority=0)
        with pytest.raises(Exception):
            BackupInstructorCreate(instructor_id=uuid.uuid4(), priority=4)

    def test_update_schema_partial(self) -> None:
        """BackupInstructorUpdate should support partial updates."""
        schema = BackupInstructorUpdate(priority=2)
        dumped = schema.model_dump(exclude_unset=True)
        assert dumped == {"priority": 2}
        assert "nickname" not in dumped
        assert "note" not in dumped

    def test_response_schema_valid(self) -> None:
        """BackupInstructorResponse should accept full data."""
        response = BackupInstructorResponse(
            id=uuid.uuid4(),
            studio_id=uuid.uuid4(),
            instructor_id=uuid.uuid4(),
            nickname="Kim",
            priority=1,
            total_completed=5,
            instructor_name="Kim Instructor",
            instructor_phone="010-1234-5678",
            instructor_categories=["pilates"],
            instructor_rating=4.5,
        )
        assert response.instructor_name == "Kim Instructor"
        assert response.total_completed == 5

    def test_response_schema_defaults(self) -> None:
        """BackupInstructorResponse should have sensible defaults."""
        response = BackupInstructorResponse(
            id=uuid.uuid4(),
            studio_id=uuid.uuid4(),
            instructor_id=uuid.uuid4(),
        )
        assert response.priority == 3
        assert response.total_completed == 0
        assert response.instructor_name is None
        assert response.instructor_phone is None

    def test_list_response_schema(self) -> None:
        """BackupInstructorListResponse should contain items and total."""
        response = BackupInstructorListResponse(items=[], total=0)
        assert response.items == []
        assert response.total == 0


# ===========================================================================
# 8. Router registration
# ===========================================================================

class TestBackupInstructorsRouter:
    """Verify the backup-instructors router is registered."""

    def test_router_registered(self) -> None:
        """The backup-instructors router should be registered in api_router."""
        from app.api.v1.router import api_router

        paths = [route.path for route in api_router.routes]
        # The prefix is /studios/me/backup-instructors
        assert any("backup-instructors" in p for p in paths)

    def test_router_has_crud_endpoints(self) -> None:
        """The router should have GET, POST, PATCH, DELETE endpoints."""
        from app.api.v1.endpoints.backup_instructors import router

        methods_found = set()
        for route in router.routes:
            if hasattr(route, "methods"):
                methods_found.update(route.methods)

        assert "GET" in methods_found
        assert "POST" in methods_found
        assert "PATCH" in methods_found
        assert "DELETE" in methods_found
