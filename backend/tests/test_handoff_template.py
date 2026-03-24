"""Tests for PilaMatch Handoff Template Service.

Covers:
1. Create template -- basic creation, field storage
2. List templates -- sorted by usage_count DESC
3. Template limit (max 20 per studio)
4. Apply template -- copy fields to handoff note, increment usage_count
5. Completeness score calculation
6. Delete template
7. Model structure validation
"""

import uuid
from decimal import Decimal
from typing import Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.handoff_template import HandoffTemplate
from app.models.handoff_note import HandoffNote
from app.services.handoff_template import (
    HandoffTemplateService,
    calculate_completeness_score,
    MAX_TEMPLATES_PER_STUDIO,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_studio_profile(
    profile_id: Optional[str] = None,
    user_id: Optional[str] = None,
) -> MagicMock:
    """Create a fake StudioProfile."""
    studio = MagicMock()
    studio.id = profile_id or str(uuid.uuid4())
    studio.user_id = user_id or str(uuid.uuid4())
    return studio


def _make_template(
    template_id: Optional[str] = None,
    studio_id: Optional[str] = None,
    name: str = "Morning Reformer",
    class_topic: str = "Reformer Basics",
    class_sequence_info: str = "Warm-up -> Footwork -> Long Stretch -> Cool Down",
    atmosphere_preference: str = "calm",
    member_caution_tags: Optional[list] = None,
    member_free_text: str = "Check posture alignment",
    equipment_notes: str = "Reformer #3 spring broken",
    additional_notes: str = "Play soft music",
    usage_count: int = 0,
) -> MagicMock:
    """Create a fake HandoffTemplate."""
    template = MagicMock(spec=HandoffTemplate)
    template.id = template_id or str(uuid.uuid4())
    template.studio_id = studio_id or str(uuid.uuid4())
    template.name = name
    template.class_topic = class_topic
    template.class_sequence_info = class_sequence_info
    template.atmosphere_preference = atmosphere_preference
    template.member_caution_tags = member_caution_tags or []
    template.member_free_text = member_free_text
    template.equipment_notes = equipment_notes
    template.additional_notes = additional_notes
    template.usage_count = usage_count
    return template


def _make_handoff_note(
    note_id: Optional[str] = None,
    job_post_id: Optional[str] = None,
    class_topic: Optional[str] = None,
    class_sequence_info: Optional[str] = None,
    atmosphere_preference: Optional[str] = None,
    member_caution_tags: Optional[list] = None,
    member_free_text: Optional[str] = None,
    equipment_notes: Optional[str] = None,
    additional_notes: Optional[str] = None,
    template_id: Optional[str] = None,
    completeness_score: Optional[Decimal] = None,
) -> MagicMock:
    """Create a fake HandoffNote."""
    note = MagicMock()
    note.id = note_id or str(uuid.uuid4())
    note.job_post_id = job_post_id or str(uuid.uuid4())
    note.class_topic = class_topic
    note.class_sequence_info = class_sequence_info
    note.atmosphere_preference = atmosphere_preference
    note.member_caution_tags = member_caution_tags or []
    note.member_free_text = member_free_text
    note.equipment_notes = equipment_notes
    note.additional_notes = additional_notes
    note.template_id = template_id
    note.completeness_score = completeness_score
    return note


# ===========================================================================
# 1. Create Template
# ===========================================================================

class TestCreateTemplate:
    """Tests for HandoffTemplateService.create_template."""

    @pytest.mark.asyncio
    async def test_create_template_basic(self) -> None:
        """Should create a template and add it to the session."""
        user_id = str(uuid.uuid4())
        studio = _make_studio_profile(user_id=user_id)

        db = AsyncMock()
        call_count = 0

        async def mock_execute(stmt):
            nonlocal call_count
            call_count += 1
            result = MagicMock()
            if call_count == 1:
                # _get_studio: select StudioProfile
                result.scalar_one_or_none.return_value = studio
            elif call_count == 2:
                # count check
                result.scalar_one.return_value = 5  # under limit
            return result

        db.execute = AsyncMock(side_effect=mock_execute)
        db.add = MagicMock()
        db.flush = AsyncMock()

        service = HandoffTemplateService(db)
        result = await service.create_template(
            user_id=user_id,
            name="Morning Reformer",
            class_topic="Reformer Basics",
            atmosphere_preference="calm",
        )

        assert isinstance(result, HandoffTemplate)
        db.add.assert_called_once()
        created = db.add.call_args[0][0]
        assert created.name == "Morning Reformer"
        assert created.class_topic == "Reformer Basics"
        assert created.studio_id == studio.id

    @pytest.mark.asyncio
    async def test_create_template_with_all_fields(self) -> None:
        """Should store all optional fields correctly."""
        user_id = str(uuid.uuid4())
        studio = _make_studio_profile(user_id=user_id)

        db = AsyncMock()
        call_count = 0

        async def mock_execute(stmt):
            nonlocal call_count
            call_count += 1
            result = MagicMock()
            if call_count == 1:
                result.scalar_one_or_none.return_value = studio
            elif call_count == 2:
                result.scalar_one.return_value = 0
            return result

        db.execute = AsyncMock(side_effect=mock_execute)
        db.add = MagicMock()
        db.flush = AsyncMock()

        service = HandoffTemplateService(db)
        result = await service.create_template(
            user_id=user_id,
            name="Full Template",
            class_topic="Mat Pilates",
            class_sequence_info="Step by step flow",
            atmosphere_preference="energetic",
            member_caution_tags=["허리_제한", "무릎_주의"],
            member_free_text="Check alignment",
            equipment_notes="Bring extra mats",
            additional_notes="Music: upbeat",
        )

        created = db.add.call_args[0][0]
        assert created.member_caution_tags == ["허리_제한", "무릎_주의"]
        assert created.equipment_notes == "Bring extra mats"


# ===========================================================================
# 2. List Templates (Sorted by usage_count DESC)
# ===========================================================================

class TestListTemplates:
    """Tests for HandoffTemplateService.list_templates."""

    @pytest.mark.asyncio
    async def test_list_returns_templates(self) -> None:
        """Should return list of templates for the studio."""
        user_id = str(uuid.uuid4())
        studio = _make_studio_profile(user_id=user_id)

        templates = [
            _make_template(studio_id=studio.id, name="Template A", usage_count=10),
            _make_template(studio_id=studio.id, name="Template B", usage_count=5),
            _make_template(studio_id=studio.id, name="Template C", usage_count=1),
        ]

        db = AsyncMock()
        call_count = 0

        async def mock_execute(stmt):
            nonlocal call_count
            call_count += 1
            result = MagicMock()
            if call_count == 1:
                # _get_studio
                result.scalar_one_or_none.return_value = studio
            elif call_count == 2:
                # select templates
                scalars = MagicMock()
                scalars.all.return_value = templates
                result.scalars.return_value = scalars
            return result

        db.execute = AsyncMock(side_effect=mock_execute)

        service = HandoffTemplateService(db)
        result = await service.list_templates(user_id)

        assert len(result) == 3
        # Should be sorted by usage_count desc (service handles ORDER BY)
        assert result[0].usage_count >= result[1].usage_count

    @pytest.mark.asyncio
    async def test_list_empty_studio(self) -> None:
        """Should return empty list for studio with no templates."""
        user_id = str(uuid.uuid4())
        studio = _make_studio_profile(user_id=user_id)

        db = AsyncMock()
        call_count = 0

        async def mock_execute(stmt):
            nonlocal call_count
            call_count += 1
            result = MagicMock()
            if call_count == 1:
                result.scalar_one_or_none.return_value = studio
            elif call_count == 2:
                scalars = MagicMock()
                scalars.all.return_value = []
                result.scalars.return_value = scalars
            return result

        db.execute = AsyncMock(side_effect=mock_execute)

        service = HandoffTemplateService(db)
        result = await service.list_templates(user_id)

        assert result == []


# ===========================================================================
# 3. Template Limit (Max 20 per Studio)
# ===========================================================================

class TestTemplateLimit:
    """Tests for the max 20 templates per studio enforcement."""

    @pytest.mark.asyncio
    async def test_creating_21st_template_raises(self) -> None:
        """Creating a 21st template should raise TEMPLATE_LIMIT_REACHED."""
        user_id = str(uuid.uuid4())
        studio = _make_studio_profile(user_id=user_id)

        db = AsyncMock()
        call_count = 0

        async def mock_execute(stmt):
            nonlocal call_count
            call_count += 1
            result = MagicMock()
            if call_count == 1:
                result.scalar_one_or_none.return_value = studio
            elif call_count == 2:
                result.scalar_one.return_value = 20  # at limit!
            return result

        db.execute = AsyncMock(side_effect=mock_execute)

        service = HandoffTemplateService(db)

        with pytest.raises(ValueError, match="TEMPLATE_LIMIT_REACHED"):
            await service.create_template(user_id=user_id, name="One Too Many")

    def test_max_templates_constant_is_20(self) -> None:
        """MAX_TEMPLATES_PER_STUDIO should be 20."""
        assert MAX_TEMPLATES_PER_STUDIO == 20

    @pytest.mark.asyncio
    async def test_creating_at_19_succeeds(self) -> None:
        """Creating the 20th template (count=19) should succeed."""
        user_id = str(uuid.uuid4())
        studio = _make_studio_profile(user_id=user_id)

        db = AsyncMock()
        call_count = 0

        async def mock_execute(stmt):
            nonlocal call_count
            call_count += 1
            result = MagicMock()
            if call_count == 1:
                result.scalar_one_or_none.return_value = studio
            elif call_count == 2:
                result.scalar_one.return_value = 19  # under limit
            return result

        db.execute = AsyncMock(side_effect=mock_execute)
        db.add = MagicMock()
        db.flush = AsyncMock()

        service = HandoffTemplateService(db)
        result = await service.create_template(user_id=user_id, name="Last One Allowed")

        assert isinstance(result, HandoffTemplate)


# ===========================================================================
# 4. Apply Template
# ===========================================================================

class TestApplyTemplate:
    """Tests for HandoffTemplateService.apply_template."""

    @pytest.mark.asyncio
    async def test_apply_copies_fields_to_note(self) -> None:
        """Applying template should copy all fields to the handoff note."""
        user_id = str(uuid.uuid4())
        studio = _make_studio_profile(user_id=user_id)
        template = _make_template(
            studio_id=studio.id,
            class_topic="Reformer Advanced",
            class_sequence_info="Footwork -> Hundred -> Long Stretch -> Cool Down",
            atmosphere_preference="focused",
            member_caution_tags=["허리_제한"],
            member_free_text="Check posture",
            equipment_notes="Use heavy springs",
            additional_notes="No music",
            usage_count=3,
        )
        note = _make_handoff_note(class_topic=None)

        db = AsyncMock()
        call_count = 0

        async def mock_execute(stmt):
            nonlocal call_count
            call_count += 1
            result = MagicMock()
            if call_count == 1:
                # _get_studio
                result.scalar_one_or_none.return_value = studio
            elif call_count == 2:
                # _get_owned_template -> select template
                result.scalar_one_or_none.return_value = template
            elif call_count == 3:
                # select handoff note
                result.scalar_one_or_none.return_value = note
            return result

        db.execute = AsyncMock(side_effect=mock_execute)
        db.flush = AsyncMock()

        service = HandoffTemplateService(db)
        result = await service.apply_template(user_id, str(template.id), str(note.job_post_id))

        assert note.class_topic == "Reformer Advanced"
        assert note.atmosphere_preference == "focused"
        assert note.member_caution_tags == ["허리_제한"]
        assert note.equipment_notes == "Use heavy springs"
        assert note.template_id == str(template.id)
        # Usage count should be incremented
        assert template.usage_count == 4

    @pytest.mark.asyncio
    async def test_apply_increments_usage_count(self) -> None:
        """apply_template should increment the template's usage_count."""
        user_id = str(uuid.uuid4())
        studio = _make_studio_profile(user_id=user_id)
        template = _make_template(studio_id=studio.id, usage_count=7)
        note = _make_handoff_note()

        db = AsyncMock()
        call_count = 0

        async def mock_execute(stmt):
            nonlocal call_count
            call_count += 1
            result = MagicMock()
            if call_count == 1:
                result.scalar_one_or_none.return_value = studio
            elif call_count == 2:
                result.scalar_one_or_none.return_value = template
            elif call_count == 3:
                result.scalar_one_or_none.return_value = note
            return result

        db.execute = AsyncMock(side_effect=mock_execute)
        db.flush = AsyncMock()

        service = HandoffTemplateService(db)
        await service.apply_template(user_id, str(template.id), str(note.job_post_id))

        assert template.usage_count == 8

    @pytest.mark.asyncio
    async def test_apply_note_not_found_raises(self) -> None:
        """Applying template when handoff note does not exist should raise error."""
        user_id = str(uuid.uuid4())
        studio = _make_studio_profile(user_id=user_id)
        template = _make_template(studio_id=studio.id)

        db = AsyncMock()
        call_count = 0

        async def mock_execute(stmt):
            nonlocal call_count
            call_count += 1
            result = MagicMock()
            if call_count == 1:
                result.scalar_one_or_none.return_value = studio
            elif call_count == 2:
                result.scalar_one_or_none.return_value = template
            elif call_count == 3:
                result.scalar_one_or_none.return_value = None  # no note
            return result

        db.execute = AsyncMock(side_effect=mock_execute)

        service = HandoffTemplateService(db)

        with pytest.raises(ValueError, match="HANDOFF_NOTE_NOT_FOUND"):
            await service.apply_template(user_id, str(template.id), "fake-job-id")


# ===========================================================================
# 5. Completeness Score Calculation
# ===========================================================================

class TestCompletenessScore:
    """Tests for calculate_completeness_score -- 0.0 to 1.0 score."""

    def test_empty_note_scores_zero(self) -> None:
        """A note with all None/empty fields should score 0.0."""
        note = _make_handoff_note(
            class_topic=None,
            class_sequence_info=None,
            atmosphere_preference=None,
            member_caution_tags=[],
            member_free_text=None,
            equipment_notes=None,
            additional_notes=None,
        )
        assert calculate_completeness_score(note) == 0.0

    def test_full_note_scores_1_0(self) -> None:
        """A note with all fields filled should score 1.0."""
        note = _make_handoff_note(
            class_topic="Reformer Basics",
            class_sequence_info="A very detailed sequence description that is more than 20 characters long",
            atmosphere_preference="calm",
            member_caution_tags=["허리_제한"],
            member_free_text=None,  # tags already fulfill member criteria
            equipment_notes="Check springs",
            additional_notes="Play music",
        )
        assert calculate_completeness_score(note) == 1.0

    def test_only_class_topic_scores_0_20(self) -> None:
        """A note with only class_topic should score 0.20."""
        note = _make_handoff_note(
            class_topic="Mat Pilates",
            class_sequence_info=None,
            atmosphere_preference=None,
            member_caution_tags=[],
            member_free_text=None,
            equipment_notes=None,
            additional_notes=None,
        )
        assert calculate_completeness_score(note) == 0.20

    def test_short_sequence_info_not_counted(self) -> None:
        """class_sequence_info shorter than 20 chars should not count."""
        note = _make_handoff_note(
            class_topic="Test",
            class_sequence_info="Short",  # < 20 chars
            atmosphere_preference=None,
            member_caution_tags=[],
            member_free_text=None,
            equipment_notes=None,
            additional_notes=None,
        )
        # Only class_topic counted = 0.20
        assert calculate_completeness_score(note) == 0.20

    def test_member_free_text_short_not_counted(self) -> None:
        """member_free_text shorter than 10 chars should not count (if no tags)."""
        note = _make_handoff_note(
            class_topic=None,
            class_sequence_info=None,
            atmosphere_preference=None,
            member_caution_tags=[],
            member_free_text="Short",  # < 10 chars
            equipment_notes=None,
            additional_notes=None,
        )
        assert calculate_completeness_score(note) == 0.0

    def test_member_free_text_long_counts(self) -> None:
        """member_free_text >= 10 chars should contribute 0.20."""
        note = _make_handoff_note(
            class_topic=None,
            class_sequence_info=None,
            atmosphere_preference=None,
            member_caution_tags=[],
            member_free_text="This is a sufficiently long note about members",
            equipment_notes=None,
            additional_notes=None,
        )
        assert calculate_completeness_score(note) == 0.20

    def test_atmosphere_preference_adds_0_15(self) -> None:
        """atmosphere_preference should contribute 0.15."""
        note = _make_handoff_note(
            class_topic=None,
            class_sequence_info=None,
            atmosphere_preference="energetic",
            member_caution_tags=[],
            member_free_text=None,
            equipment_notes=None,
            additional_notes=None,
        )
        assert calculate_completeness_score(note) == 0.15

    def test_equipment_notes_adds_0_10(self) -> None:
        """equipment_notes should contribute 0.10."""
        note = _make_handoff_note(
            class_topic=None,
            class_sequence_info=None,
            atmosphere_preference=None,
            member_caution_tags=[],
            member_free_text=None,
            equipment_notes="Check springs",
            additional_notes=None,
        )
        assert calculate_completeness_score(note) == 0.10

    def test_additional_notes_adds_0_10(self) -> None:
        """additional_notes should contribute 0.10."""
        note = _make_handoff_note(
            class_topic=None,
            class_sequence_info=None,
            atmosphere_preference=None,
            member_caution_tags=[],
            member_free_text=None,
            equipment_notes=None,
            additional_notes="Bring towels",
        )
        assert calculate_completeness_score(note) == 0.10

    def test_score_is_rounded_to_2_decimals(self) -> None:
        """Score should be rounded to 2 decimal places."""
        note = _make_handoff_note(
            class_topic="Test",
            class_sequence_info=None,
            atmosphere_preference="calm",
            member_caution_tags=[],
            member_free_text=None,
            equipment_notes=None,
            additional_notes=None,
        )
        score = calculate_completeness_score(note)
        # 0.20 + 0.15 = 0.35
        assert score == 0.35
        assert isinstance(score, float)


# ===========================================================================
# 6. Delete Template
# ===========================================================================

class TestDeleteTemplate:
    """Tests for HandoffTemplateService.delete_template."""

    @pytest.mark.asyncio
    async def test_delete_existing_template(self) -> None:
        """Should delete the template from the session."""
        user_id = str(uuid.uuid4())
        studio = _make_studio_profile(user_id=user_id)
        template = _make_template(studio_id=studio.id)

        db = AsyncMock()
        call_count = 0

        async def mock_execute(stmt):
            nonlocal call_count
            call_count += 1
            result = MagicMock()
            if call_count == 1:
                # _get_studio
                result.scalar_one_or_none.return_value = studio
            elif call_count == 2:
                # _get_owned_template
                result.scalar_one_or_none.return_value = template
            return result

        db.execute = AsyncMock(side_effect=mock_execute)
        db.delete = AsyncMock()
        db.flush = AsyncMock()

        service = HandoffTemplateService(db)
        await service.delete_template(user_id, str(template.id))

        db.delete.assert_awaited_once_with(template)

    @pytest.mark.asyncio
    async def test_delete_nonexistent_template_raises(self) -> None:
        """Should raise TEMPLATE_NOT_FOUND if template does not exist."""
        user_id = str(uuid.uuid4())
        studio = _make_studio_profile(user_id=user_id)

        db = AsyncMock()
        call_count = 0

        async def mock_execute(stmt):
            nonlocal call_count
            call_count += 1
            result = MagicMock()
            if call_count == 1:
                result.scalar_one_or_none.return_value = studio
            elif call_count == 2:
                result.scalar_one_or_none.return_value = None  # not found
            return result

        db.execute = AsyncMock(side_effect=mock_execute)

        service = HandoffTemplateService(db)

        with pytest.raises(ValueError, match="TEMPLATE_NOT_FOUND"):
            await service.delete_template(user_id, "fake-template-id")

    @pytest.mark.asyncio
    async def test_delete_other_studios_template_raises(self) -> None:
        """Should raise TEMPLATE_NOT_FOUND when trying to delete another studio's template."""
        user_id = str(uuid.uuid4())
        studio = _make_studio_profile(user_id=user_id)
        # Template belongs to a different studio
        other_studio_template = _make_template(studio_id=str(uuid.uuid4()))

        db = AsyncMock()
        call_count = 0

        async def mock_execute(stmt):
            nonlocal call_count
            call_count += 1
            result = MagicMock()
            if call_count == 1:
                result.scalar_one_or_none.return_value = studio
            elif call_count == 2:
                # Template lookup includes studio_id check, returns None
                result.scalar_one_or_none.return_value = None
            return result

        db.execute = AsyncMock(side_effect=mock_execute)

        service = HandoffTemplateService(db)

        with pytest.raises(ValueError, match="TEMPLATE_NOT_FOUND"):
            await service.delete_template(user_id, str(other_studio_template.id))


# ===========================================================================
# 7. Studio Not Found
# ===========================================================================

class TestStudioNotFound:
    """Tests for operations when studio profile is not found."""

    @pytest.mark.asyncio
    async def test_create_without_studio_raises(self) -> None:
        """Creating template without studio profile should raise STUDIO_NOT_FOUND."""
        db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=result)

        service = HandoffTemplateService(db)

        with pytest.raises(ValueError, match="STUDIO_NOT_FOUND"):
            await service.create_template(user_id=str(uuid.uuid4()), name="Test")

    @pytest.mark.asyncio
    async def test_list_without_studio_raises(self) -> None:
        """Listing templates without studio profile should raise STUDIO_NOT_FOUND."""
        db = AsyncMock()
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=result)

        service = HandoffTemplateService(db)

        with pytest.raises(ValueError, match="STUDIO_NOT_FOUND"):
            await service.list_templates(user_id=str(uuid.uuid4()))


# ===========================================================================
# 8. Model Structure Validation
# ===========================================================================

class TestHandoffTemplateModel:
    """Tests for HandoffTemplate model structure."""

    def test_table_name(self) -> None:
        """Table name should be 'handoff_templates'."""
        assert HandoffTemplate.__tablename__ == "handoff_templates"

    def test_has_studio_id_column(self) -> None:
        """Model should have studio_id foreign key column."""
        assert "studio_id" in HandoffTemplate.__table__.columns

    def test_has_name_column(self) -> None:
        """Model should have name column."""
        assert "name" in HandoffTemplate.__table__.columns

    def test_name_max_length_100(self) -> None:
        """name column should have String(100)."""
        col = HandoffTemplate.__table__.columns["name"]
        assert col.type.length == 100

    def test_has_class_topic_column(self) -> None:
        """Model should have class_topic column."""
        assert "class_topic" in HandoffTemplate.__table__.columns

    def test_has_usage_count_column(self) -> None:
        """Model should have usage_count column."""
        assert "usage_count" in HandoffTemplate.__table__.columns

    def test_usage_count_defaults_to_0(self) -> None:
        """usage_count should default to 0."""
        col = HandoffTemplate.__table__.columns["usage_count"]
        assert col.default is not None
        assert col.default.arg == 0

    def test_has_member_caution_tags_column(self) -> None:
        """Model should have member_caution_tags JSON column."""
        assert "member_caution_tags" in HandoffTemplate.__table__.columns

    def test_has_studio_relationship(self) -> None:
        """Model should have a 'studio' relationship."""
        assert hasattr(HandoffTemplate, "studio")
