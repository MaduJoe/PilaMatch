"""Unit tests for Handoff Note feature.

Covers:
1. Model tests — column existence, table name, relationship
2. Schema tests — field validation, public vs full response
3. Service tests — create_or_update (upsert), get_by_job_post, delete
4. Visibility/access rule tests — studio owner, accepted instructor, public viewer
"""

import uuid
from datetime import datetime
from typing import Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.handoff_note import HandoffNote
from app.schemas.handoff_note import (
    HandoffNoteCreate,
    HandoffNoteUpdate,
    HandoffNoteFullResponse,
    HandoffNotePublicResponse,
)
from app.services.handoff_note import HandoffNoteService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_handoff_note(
    note_id: Optional[uuid.UUID] = None,
    job_post_id: Optional[uuid.UUID] = None,
    author_user_id: Optional[uuid.UUID] = None,
    class_topic: str = "Reformer Basics",
    class_sequence_info: str = "Warm-up -> Footwork -> Long Stretch",
    atmosphere_preference: str = "calm",
    additional_notes: str = "Play soft music",
    member_notes: str = "Member A has lower back injury",
    equipment_notes: str = "Reformer #3 spring broken",
) -> MagicMock:
    """Create a fake HandoffNote for tests."""
    note = MagicMock(spec=HandoffNote)
    note.id = note_id or uuid.uuid4()
    note.job_post_id = job_post_id or uuid.uuid4()
    note.author_user_id = author_user_id or uuid.uuid4()
    note.class_topic = class_topic
    note.class_sequence_info = class_sequence_info
    note.atmosphere_preference = atmosphere_preference
    note.additional_notes = additional_notes
    note.member_notes = member_notes
    note.equipment_notes = equipment_notes
    note.created_at = datetime(2026, 3, 1, 10, 0, 0)
    note.updated_at = datetime(2026, 3, 1, 10, 0, 0)
    return note


def _make_create_data(**kwargs) -> HandoffNoteCreate:
    """Build HandoffNoteCreate with reasonable defaults."""
    defaults = dict(
        class_topic="Reformer Basics",
        class_sequence_info="Warm-up -> Footwork -> Long Stretch",
        atmosphere_preference="calm",
        additional_notes="Play soft music",
        member_notes="Member A has lower back injury",
        equipment_notes="Reformer #3 spring broken",
    )
    defaults.update(kwargs)
    return HandoffNoteCreate(**defaults)


# ===========================================================================
# 1. Model tests
# ===========================================================================

class TestHandoffNoteModel:
    """Verify HandoffNote model columns and relationships."""

    def test_table_name(self) -> None:
        """Table name should be 'handoff_notes'."""
        assert HandoffNote.__tablename__ == "handoff_notes"

    def test_has_class_topic_column(self) -> None:
        """Model should have class_topic column."""
        assert "class_topic" in HandoffNote.__table__.columns

    def test_has_class_sequence_info_column(self) -> None:
        """Model should have class_sequence_info column."""
        assert "class_sequence_info" in HandoffNote.__table__.columns

    def test_has_atmosphere_preference_column(self) -> None:
        """Model should have atmosphere_preference column."""
        assert "atmosphere_preference" in HandoffNote.__table__.columns

    def test_has_additional_notes_column(self) -> None:
        """Model should have additional_notes column."""
        assert "additional_notes" in HandoffNote.__table__.columns

    def test_has_member_notes_column(self) -> None:
        """Model should have member_notes (sensitive) column."""
        assert "member_notes" in HandoffNote.__table__.columns

    def test_has_equipment_notes_column(self) -> None:
        """Model should have equipment_notes (sensitive) column."""
        assert "equipment_notes" in HandoffNote.__table__.columns

    def test_has_job_post_id_column(self) -> None:
        """Model should have job_post_id foreign key column."""
        assert "job_post_id" in HandoffNote.__table__.columns

    def test_has_author_user_id_column(self) -> None:
        """Model should have author_user_id foreign key column."""
        assert "author_user_id" in HandoffNote.__table__.columns

    def test_job_post_id_is_unique(self) -> None:
        """job_post_id column should have unique constraint (one note per job post)."""
        col = HandoffNote.__table__.columns["job_post_id"]
        assert col.unique is True

    def test_job_post_id_not_nullable(self) -> None:
        """job_post_id column should not be nullable."""
        col = HandoffNote.__table__.columns["job_post_id"]
        assert col.nullable is False

    def test_job_post_relationship_exists(self) -> None:
        """HandoffNote should have a 'job_post' relationship."""
        assert hasattr(HandoffNote, "job_post")

    def test_author_relationship_exists(self) -> None:
        """HandoffNote should have an 'author' relationship."""
        assert hasattr(HandoffNote, "author")

    def test_job_post_back_populates_handoff_note(self) -> None:
        """JobPost model should have handoff_note relationship (uselist=False)."""
        from app.models.job_post import JobPost

        assert hasattr(JobPost, "handoff_note")
        # Verify it is a single-object relationship (uselist=False)
        prop = JobPost.__mapper__.relationships["handoff_note"]
        assert prop.uselist is False


# ===========================================================================
# 2. Schema tests
# ===========================================================================

class TestHandoffNoteSchemas:
    """Verify Pydantic schema behavior."""

    def test_create_all_fields_optional(self) -> None:
        """HandoffNoteCreate should accept an empty payload (all fields optional)."""
        schema = HandoffNoteCreate()
        assert schema.class_topic is None
        assert schema.class_sequence_info is None
        assert schema.atmosphere_preference is None
        assert schema.additional_notes is None
        assert schema.member_notes is None
        assert schema.equipment_notes is None

    def test_create_with_all_fields(self) -> None:
        """HandoffNoteCreate should accept all fields."""
        schema = _make_create_data()
        assert schema.class_topic == "Reformer Basics"
        assert schema.member_notes == "Member A has lower back injury"

    def test_create_class_topic_max_length(self) -> None:
        """class_topic should enforce max_length=200."""
        fields = HandoffNoteCreate.model_fields
        assert fields["class_topic"].metadata[0].max_length == 200

    def test_create_atmosphere_preference_max_length(self) -> None:
        """atmosphere_preference should enforce max_length=50."""
        fields = HandoffNoteCreate.model_fields
        assert fields["atmosphere_preference"].metadata[0].max_length == 50

    def test_update_inherits_create(self) -> None:
        """HandoffNoteUpdate should have the same fields as HandoffNoteCreate."""
        create_fields = set(HandoffNoteCreate.model_fields.keys())
        update_fields = set(HandoffNoteUpdate.model_fields.keys())
        assert create_fields == update_fields

    def test_public_response_excludes_member_notes(self) -> None:
        """HandoffNotePublicResponse should NOT have member_notes field."""
        fields = HandoffNotePublicResponse.model_fields
        assert "member_notes" not in fields

    def test_public_response_excludes_equipment_notes(self) -> None:
        """HandoffNotePublicResponse should NOT have equipment_notes field."""
        fields = HandoffNotePublicResponse.model_fields
        assert "equipment_notes" not in fields

    def test_public_response_has_sensitive_info_flag(self) -> None:
        """HandoffNotePublicResponse should have has_sensitive_info boolean field."""
        fields = HandoffNotePublicResponse.model_fields
        assert "has_sensitive_info" in fields

    def test_public_response_has_sensitive_info_default_false(self) -> None:
        """has_sensitive_info should default to False."""
        schema = HandoffNotePublicResponse(
            id=uuid.uuid4(),
            job_post_id=uuid.uuid4(),
        )
        assert schema.has_sensitive_info is False

    def test_full_response_includes_member_notes(self) -> None:
        """HandoffNoteFullResponse should have member_notes field."""
        fields = HandoffNoteFullResponse.model_fields
        assert "member_notes" in fields

    def test_full_response_includes_equipment_notes(self) -> None:
        """HandoffNoteFullResponse should have equipment_notes field."""
        fields = HandoffNoteFullResponse.model_fields
        assert "equipment_notes" in fields

    def test_full_response_does_not_have_has_sensitive_info(self) -> None:
        """HandoffNoteFullResponse should NOT have has_sensitive_info flag."""
        fields = HandoffNoteFullResponse.model_fields
        assert "has_sensitive_info" not in fields

    def test_public_response_from_attributes(self) -> None:
        """HandoffNotePublicResponse should support from_attributes (ORM mode)."""
        assert HandoffNotePublicResponse.model_config.get("from_attributes") is True

    def test_full_response_from_attributes(self) -> None:
        """HandoffNoteFullResponse should support from_attributes (ORM mode)."""
        assert HandoffNoteFullResponse.model_config.get("from_attributes") is True


# ===========================================================================
# 3. Service tests
# ===========================================================================

class TestHandoffNoteServiceCreate:
    """Tests for HandoffNoteService.create_or_update (create path)."""

    async def test_create_new_note(self) -> None:
        """Creates a new HandoffNote when none exists for the job post."""
        job_post_id = uuid.uuid4()
        author_id = uuid.uuid4()
        data = _make_create_data()

        db = AsyncMock()
        # Query returns no existing note
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=result_mock)
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()

        service = HandoffNoteService(db)
        result = await service.create_or_update(job_post_id, author_id, data)

        # db.add should have been called with the new note
        db.add.assert_called_once()
        created_obj = db.add.call_args[0][0]
        assert isinstance(created_obj, HandoffNote)
        assert created_obj.job_post_id == job_post_id
        assert created_obj.author_user_id == author_id
        assert created_obj.class_topic == "Reformer Basics"
        assert created_obj.member_notes == "Member A has lower back injury"

    async def test_create_commits_to_db(self) -> None:
        """Service should commit and refresh after creating."""
        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=result_mock)
        db.add = MagicMock()
        db.commit = AsyncMock()
        db.refresh = AsyncMock()

        service = HandoffNoteService(db)
        await service.create_or_update(uuid.uuid4(), uuid.uuid4(), _make_create_data())

        db.commit.assert_awaited_once()
        db.refresh.assert_awaited_once()


class TestHandoffNoteServiceUpdate:
    """Tests for HandoffNoteService.create_or_update (update path)."""

    async def test_update_existing_note(self) -> None:
        """Updates an existing note's fields when one already exists."""
        job_post_id = uuid.uuid4()
        author_id = uuid.uuid4()
        existing_note = _make_handoff_note(job_post_id=job_post_id)

        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = existing_note
        db.execute = AsyncMock(return_value=result_mock)
        db.commit = AsyncMock()
        db.refresh = AsyncMock()

        update_data = HandoffNoteCreate(class_topic="Advanced Reformer")
        service = HandoffNoteService(db)
        result = await service.create_or_update(job_post_id, author_id, update_data)

        # Should NOT call db.add for updates
        db.add.assert_not_called()
        # Should update the field on the existing object
        assert existing_note.class_topic == "Advanced Reformer"

    async def test_upsert_does_not_create_duplicate(self) -> None:
        """When note exists, create_or_update should not add a new record."""
        existing_note = _make_handoff_note()

        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = existing_note
        db.execute = AsyncMock(return_value=result_mock)
        db.commit = AsyncMock()
        db.refresh = AsyncMock()

        service = HandoffNoteService(db)
        await service.create_or_update(
            existing_note.job_post_id,
            existing_note.author_user_id,
            _make_create_data(class_topic="Changed"),
        )

        db.add.assert_not_called()

    async def test_update_commits_to_db(self) -> None:
        """Service should commit and refresh after updating."""
        existing_note = _make_handoff_note()

        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = existing_note
        db.execute = AsyncMock(return_value=result_mock)
        db.commit = AsyncMock()
        db.refresh = AsyncMock()

        service = HandoffNoteService(db)
        await service.create_or_update(
            existing_note.job_post_id,
            uuid.uuid4(),
            _make_create_data(),
        )

        db.commit.assert_awaited_once()
        db.refresh.assert_awaited_once()


class TestHandoffNoteServiceGetByJobPost:
    """Tests for HandoffNoteService.get_by_job_post."""

    async def test_returns_note_when_exists(self) -> None:
        """Returns the HandoffNote when one exists for the job post."""
        job_post_id = uuid.uuid4()
        existing_note = _make_handoff_note(job_post_id=job_post_id)

        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = existing_note
        db.execute = AsyncMock(return_value=result_mock)

        service = HandoffNoteService(db)
        result = await service.get_by_job_post(job_post_id)

        assert result is existing_note
        assert result.job_post_id == job_post_id

    async def test_returns_none_when_not_exists(self) -> None:
        """Returns None when no note exists for the job post."""
        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=result_mock)

        service = HandoffNoteService(db)
        result = await service.get_by_job_post(uuid.uuid4())

        assert result is None


class TestHandoffNoteServiceDelete:
    """Tests for HandoffNoteService.delete."""

    async def test_delete_existing_note_returns_true(self) -> None:
        """Returns True when a note is found and deleted."""
        job_post_id = uuid.uuid4()
        existing_note = _make_handoff_note(job_post_id=job_post_id)

        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = existing_note
        db.execute = AsyncMock(return_value=result_mock)
        db.delete = AsyncMock()
        db.commit = AsyncMock()

        service = HandoffNoteService(db)
        result = await service.delete(job_post_id)

        assert result is True
        db.delete.assert_awaited_once_with(existing_note)
        db.commit.assert_awaited_once()

    async def test_delete_nonexistent_note_returns_false(self) -> None:
        """Returns False when no note exists for the job post."""
        db = AsyncMock()
        result_mock = MagicMock()
        result_mock.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=result_mock)

        service = HandoffNoteService(db)
        result = await service.delete(uuid.uuid4())

        assert result is False
        db.delete.assert_not_awaited()
        db.commit.assert_not_awaited()


# ===========================================================================
# 4. Visibility / Access Rule tests
# ===========================================================================

class TestHandoffNoteVisibility:
    """Test that public responses hide sensitive data and full responses include it."""

    def test_public_response_does_not_leak_member_notes(self) -> None:
        """PublicResponse constructed from a note should not contain member_notes."""
        note = _make_handoff_note(
            member_notes="Sensitive member info",
            equipment_notes="Sensitive equipment info",
        )
        public = HandoffNotePublicResponse(
            id=note.id,
            job_post_id=note.job_post_id,
            class_topic=note.class_topic,
            class_sequence_info=note.class_sequence_info,
            atmosphere_preference=note.atmosphere_preference,
            additional_notes=note.additional_notes,
            has_sensitive_info=bool(note.member_notes or note.equipment_notes),
        )

        response_dict = public.model_dump()
        assert "member_notes" not in response_dict
        assert "equipment_notes" not in response_dict
        assert public.has_sensitive_info is True

    def test_public_response_has_sensitive_info_false_when_no_sensitive_data(self) -> None:
        """has_sensitive_info should be False when member_notes and equipment_notes are empty."""
        note = _make_handoff_note(member_notes=None, equipment_notes=None)
        public = HandoffNotePublicResponse(
            id=note.id,
            job_post_id=note.job_post_id,
            class_topic=note.class_topic,
            has_sensitive_info=bool(note.member_notes or note.equipment_notes),
        )
        assert public.has_sensitive_info is False

    def test_public_response_has_sensitive_info_true_member_only(self) -> None:
        """has_sensitive_info True when only member_notes is set."""
        note = _make_handoff_note(member_notes="Sensitive", equipment_notes=None)
        has_sensitive = bool(note.member_notes or note.equipment_notes)
        assert has_sensitive is True

    def test_public_response_has_sensitive_info_true_equipment_only(self) -> None:
        """has_sensitive_info True when only equipment_notes is set."""
        note = _make_handoff_note(member_notes=None, equipment_notes="Broken spring")
        has_sensitive = bool(note.member_notes or note.equipment_notes)
        assert has_sensitive is True

    def test_full_response_includes_all_sensitive_fields(self) -> None:
        """FullResponse should include member_notes and equipment_notes."""
        note_id = uuid.uuid4()
        jp_id = uuid.uuid4()
        full = HandoffNoteFullResponse(
            id=note_id,
            job_post_id=jp_id,
            class_topic="Test Topic",
            member_notes="Sensitive member info",
            equipment_notes="Sensitive equipment info",
        )

        assert full.member_notes == "Sensitive member info"
        assert full.equipment_notes == "Sensitive equipment info"

    def test_full_response_model_dump_contains_sensitive_keys(self) -> None:
        """Full response model_dump should have member_notes and equipment_notes keys."""
        full = HandoffNoteFullResponse(
            id=uuid.uuid4(),
            job_post_id=uuid.uuid4(),
            member_notes="Private",
            equipment_notes="Private",
        )

        dumped = full.model_dump()
        assert "member_notes" in dumped
        assert "equipment_notes" in dumped

    def test_public_vs_full_field_difference(self) -> None:
        """Public schema should have exactly 2 fewer content fields + 1 extra flag vs Full."""
        public_fields = set(HandoffNotePublicResponse.model_fields.keys())
        full_fields = set(HandoffNoteFullResponse.model_fields.keys())

        # Fields in Full but not in Public
        full_only = full_fields - public_fields
        assert "member_notes" in full_only
        assert "equipment_notes" in full_only

        # Fields in Public but not in Full
        public_only = public_fields - full_fields
        assert "has_sensitive_info" in public_only


class TestHandoffNoteVisibilityScenarios:
    """Integration-style tests simulating the endpoint visibility logic.

    These replicate the access control in get_handoff_note endpoint
    without actually calling the HTTP endpoint, using the same logic.
    """

    def _resolve_response(
        self,
        note: MagicMock,
        is_studio_owner: bool = False,
        is_accepted_instructor: bool = False,
    ):
        """Simulate the visibility resolution logic from the endpoint."""
        if is_studio_owner or is_accepted_instructor:
            return HandoffNoteFullResponse.model_validate(note)
        else:
            return HandoffNotePublicResponse(
                id=note.id,
                job_post_id=note.job_post_id,
                class_topic=note.class_topic,
                class_sequence_info=note.class_sequence_info,
                atmosphere_preference=note.atmosphere_preference,
                additional_notes=note.additional_notes,
                has_sensitive_info=bool(note.member_notes or note.equipment_notes),
                created_at=note.created_at,
                updated_at=note.updated_at,
            )

    def test_studio_owner_sees_full_response(self) -> None:
        """Studio owner should get FullResponse with all sensitive fields."""
        note = _make_handoff_note()
        resp = self._resolve_response(note, is_studio_owner=True)

        assert isinstance(resp, HandoffNoteFullResponse)
        assert resp.member_notes == note.member_notes
        assert resp.equipment_notes == note.equipment_notes

    def test_accepted_instructor_sees_full_response(self) -> None:
        """Accepted instructor with contact_revealed=True should get FullResponse."""
        note = _make_handoff_note()
        resp = self._resolve_response(note, is_accepted_instructor=True)

        assert isinstance(resp, HandoffNoteFullResponse)
        assert resp.member_notes == note.member_notes
        assert resp.equipment_notes == note.equipment_notes

    def test_non_accepted_instructor_sees_public_response(self) -> None:
        """Non-accepted instructor should get PublicResponse without sensitive data."""
        note = _make_handoff_note(
            member_notes="Secret member data",
            equipment_notes="Secret equipment data",
        )
        resp = self._resolve_response(
            note, is_studio_owner=False, is_accepted_instructor=False
        )

        assert isinstance(resp, HandoffNotePublicResponse)
        assert resp.has_sensitive_info is True
        dumped = resp.model_dump()
        assert "member_notes" not in dumped
        assert "equipment_notes" not in dumped

    def test_public_viewer_does_not_see_sensitive_data(self) -> None:
        """Random authenticated user should not see sensitive fields."""
        note = _make_handoff_note()
        resp = self._resolve_response(
            note, is_studio_owner=False, is_accepted_instructor=False
        )

        assert isinstance(resp, HandoffNotePublicResponse)
        dumped = resp.model_dump()
        assert "member_notes" not in dumped
        assert "equipment_notes" not in dumped

    def test_public_response_preserves_non_sensitive_fields(self) -> None:
        """PublicResponse should still show class_topic, sequence, atmosphere, etc."""
        note = _make_handoff_note(
            class_topic="Mat Pilates",
            class_sequence_info="Step 1 -> Step 2",
            atmosphere_preference="energetic",
            additional_notes="Bring towels",
        )
        resp = self._resolve_response(
            note, is_studio_owner=False, is_accepted_instructor=False
        )

        assert resp.class_topic == "Mat Pilates"
        assert resp.class_sequence_info == "Step 1 -> Step 2"
        assert resp.atmosphere_preference == "energetic"
        assert resp.additional_notes == "Bring towels"

    def test_no_sensitive_data_results_in_has_sensitive_info_false(self) -> None:
        """PublicResponse should show has_sensitive_info=False when no sensitive data."""
        note = _make_handoff_note(member_notes=None, equipment_notes=None)
        resp = self._resolve_response(
            note, is_studio_owner=False, is_accepted_instructor=False
        )

        assert isinstance(resp, HandoffNotePublicResponse)
        assert resp.has_sensitive_info is False
