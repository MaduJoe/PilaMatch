"""Unit tests for Phase 2: Style Matching.

Covers:
1. _calculate_style_score function (neutral, partial, full match, no overlap)
2. calculate_matching_score with style data (weight selection, breakdown)
3. Backward compatibility (no style data -> original weights)
4. Model columns exist (teaching_style on InstructorProfile, preferred_style on JobPost)
5. Schema fields include style data
"""

import uuid
from decimal import Decimal
from typing import Optional
from unittest.mock import MagicMock

import pytest

from app.services.matching import (
    _calculate_style_score,
    calculate_matching_score,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_instructor(
    available_regions: Optional[list] = None,
    experience_years: int = 5,
    certifications: Optional[list] = None,
    hourly_rate_min: Decimal = Decimal("30000"),
    hourly_rate_max: Decimal = Decimal("50000"),
    latitude: Optional[Decimal] = None,
    longitude: Optional[Decimal] = None,
    teaching_style: Optional[dict] = None,
) -> MagicMock:
    """Create a fake InstructorProfile for matching tests."""
    profile = MagicMock()
    profile.id = uuid.uuid4()
    profile.user_id = uuid.uuid4()
    profile.display_name = "Style Instructor"
    profile.experience_years = experience_years
    profile.available_regions = available_regions or ["서울 강남"]
    profile.hourly_rate_min = hourly_rate_min
    profile.hourly_rate_max = hourly_rate_max
    profile.certifications = certifications or []
    profile.latitude = latitude
    profile.longitude = longitude
    profile.teaching_style = teaching_style
    return profile


def _make_job(
    region: str = "서울 강남",
    required_experience_years: int = 3,
    required_certifications: Optional[list] = None,
    hourly_rate: Decimal = Decimal("40000"),
    latitude: Optional[Decimal] = None,
    longitude: Optional[Decimal] = None,
    preferred_style: Optional[dict] = None,
) -> MagicMock:
    """Create a fake JobPost for matching tests."""
    job = MagicMock()
    job.id = uuid.uuid4()
    job.studio_id = uuid.uuid4()
    job.region = region
    job.required_experience_years = required_experience_years
    job.required_certifications = required_certifications or []
    job.hourly_rate = hourly_rate
    job.latitude = latitude
    job.longitude = longitude
    job.preferred_style = preferred_style
    return job


# ===========================================================================
# 1. _calculate_style_score unit tests
# ===========================================================================

class TestCalculateStyleScore:
    """Tests for the _calculate_style_score internal function."""

    def test_neutral_when_instructor_style_empty(self) -> None:
        """Returns 50 when instructor has no style data."""
        score = _calculate_style_score({}, {"correction_style": "gentle"})
        assert score == 50

    def test_neutral_when_job_style_empty(self) -> None:
        """Returns 50 when job has no style data."""
        score = _calculate_style_score({"correction_style": "gentle"}, {})
        assert score == 50

    def test_neutral_when_both_empty(self) -> None:
        """Returns 50 when both have no style data."""
        score = _calculate_style_score({}, {})
        assert score == 50

    def test_neutral_when_no_overlapping_keys(self) -> None:
        """Returns 50 when keys don't overlap at all."""
        score = _calculate_style_score(
            {"music_preference": "calm"},
            {"correction_style": "gentle"},
        )
        assert score == 50

    def test_full_match_single_key(self) -> None:
        """Returns 100 when the single comparable key matches."""
        score = _calculate_style_score(
            {"correction_style": "gentle"},
            {"correction_style": "gentle"},
        )
        assert score == 100

    def test_full_match_multiple_keys(self) -> None:
        """Returns 100 when all comparable keys match."""
        instructor_style = {
            "correction_style": "gentle",
            "class_atmosphere": "calm",
            "intensity_level": "medium",
        }
        job_style = {
            "correction_style": "gentle",
            "class_atmosphere": "calm",
            "intensity_level": "medium",
        }
        score = _calculate_style_score(instructor_style, job_style)
        assert score == 100

    def test_no_match_all_different(self) -> None:
        """Returns 0 when no comparable keys match."""
        instructor_style = {
            "correction_style": "strict",
            "class_atmosphere": "energetic",
            "intensity_level": "high",
        }
        job_style = {
            "correction_style": "gentle",
            "class_atmosphere": "calm",
            "intensity_level": "low",
        }
        score = _calculate_style_score(instructor_style, job_style)
        assert score == 0

    def test_partial_match(self) -> None:
        """Returns correct partial score (2/3 = 66)."""
        instructor_style = {
            "correction_style": "gentle",
            "class_atmosphere": "calm",
            "intensity_level": "high",  # mismatch
        }
        job_style = {
            "correction_style": "gentle",
            "class_atmosphere": "calm",
            "intensity_level": "low",
        }
        score = _calculate_style_score(instructor_style, job_style)
        assert score == 66  # int(2/3 * 100) = 66

    def test_instructor_has_extra_keys(self) -> None:
        """Extra instructor keys are ignored; only job's keys matter for overlap."""
        instructor_style = {
            "correction_style": "gentle",
            "music_preference": "jazz",  # not in job
        }
        job_style = {
            "correction_style": "gentle",
        }
        score = _calculate_style_score(instructor_style, job_style)
        assert score == 100  # 1 comparable key, 1 match

    def test_job_has_extra_keys(self) -> None:
        """Extra job keys are ignored if instructor doesn't have them."""
        instructor_style = {
            "correction_style": "gentle",
        }
        job_style = {
            "correction_style": "gentle",
            "class_atmosphere": "calm",  # not in instructor
        }
        score = _calculate_style_score(instructor_style, job_style)
        assert score == 100  # 1 comparable key, 1 match


# ===========================================================================
# 2. calculate_matching_score with style (no distance)
# ===========================================================================

class TestMatchingScoreStyleOnly:
    """Matching with style data but no distance data."""

    def test_style_only_weights(self) -> None:
        """When has_style=True and has_distance=False, style-only weights apply."""
        instructor = _make_instructor(
            teaching_style={"correction_style": "gentle", "class_atmosphere": "calm"},
            latitude=None,
            longitude=None,
        )
        job = _make_job(
            preferred_style={"correction_style": "gentle", "class_atmosphere": "calm"},
            latitude=None,
            longitude=None,
        )

        result = calculate_matching_score(instructor, job)

        assert "style" in result["breakdown"]
        assert result["breakdown"]["style"]["weight"] == 20
        assert result["breakdown"]["region"]["weight"] == 25
        assert result["breakdown"]["experience"]["weight"] == 20
        assert result["breakdown"]["certifications"]["weight"] == 20
        assert result["breakdown"]["rate"]["weight"] == 15
        assert "distance" not in result["breakdown"]

    def test_style_only_weights_sum_to_100(self) -> None:
        """Weights sum to 100 when only style data is present."""
        instructor = _make_instructor(
            teaching_style={"correction_style": "gentle"},
        )
        job = _make_job(
            preferred_style={"correction_style": "gentle"},
        )

        result = calculate_matching_score(instructor, job)
        total_weight = sum(v["weight"] for v in result["breakdown"].values())
        assert total_weight == 100

    def test_style_score_in_breakdown(self) -> None:
        """Style score appears correctly in the breakdown."""
        instructor = _make_instructor(
            teaching_style={"correction_style": "gentle", "intensity_level": "high"},
        )
        job = _make_job(
            preferred_style={"correction_style": "gentle", "intensity_level": "low"},
        )

        result = calculate_matching_score(instructor, job)

        assert result["breakdown"]["style"]["score"] == 50  # 1/2 match


# ===========================================================================
# 3. calculate_matching_score with style + distance
# ===========================================================================

class TestMatchingScoreDistanceAndStyle:
    """Matching with both distance and style data."""

    def test_distance_and_style_weights(self) -> None:
        """When both distance and style available, 6-factor weights apply."""
        instructor = _make_instructor(
            latitude=Decimal("37.4979"),
            longitude=Decimal("127.0276"),
            teaching_style={"correction_style": "gentle"},
        )
        job = _make_job(
            latitude=Decimal("37.4990"),
            longitude=Decimal("127.0280"),
            preferred_style={"correction_style": "gentle"},
        )

        result = calculate_matching_score(instructor, job)

        assert "distance" in result["breakdown"]
        assert "style" in result["breakdown"]
        assert result["breakdown"]["distance"]["weight"] == 25
        assert result["breakdown"]["style"]["weight"] == 20
        assert result["breakdown"]["region"]["weight"] == 10
        assert result["breakdown"]["experience"]["weight"] == 20
        assert result["breakdown"]["certifications"]["weight"] == 15
        assert result["breakdown"]["rate"]["weight"] == 10

    def test_distance_and_style_weights_sum_to_100(self) -> None:
        """Weights sum to 100 when both distance and style present."""
        instructor = _make_instructor(
            latitude=Decimal("37.4979"),
            longitude=Decimal("127.0276"),
            teaching_style={"correction_style": "gentle"},
        )
        job = _make_job(
            latitude=Decimal("37.4990"),
            longitude=Decimal("127.0280"),
            preferred_style={"correction_style": "gentle"},
        )

        result = calculate_matching_score(instructor, job)
        total_weight = sum(v["weight"] for v in result["breakdown"].values())
        assert total_weight == 100


# ===========================================================================
# 4. Backward compatibility
# ===========================================================================

class TestMatchingScoreBackwardCompatibility:
    """Ensure no style data preserves original 4-factor weights."""

    def test_no_style_preserves_original_weights(self) -> None:
        """With no style data (None), original 4-factor weights are unchanged."""
        instructor = _make_instructor(
            teaching_style=None,
            latitude=None,
            longitude=None,
        )
        job = _make_job(
            preferred_style=None,
            latitude=None,
            longitude=None,
        )

        result = calculate_matching_score(instructor, job)

        assert "style" not in result["breakdown"]
        assert result["breakdown"]["region"]["weight"] == 30
        assert result["breakdown"]["experience"]["weight"] == 25
        assert result["breakdown"]["certifications"]["weight"] == 25
        assert result["breakdown"]["rate"]["weight"] == 20

    def test_empty_dict_style_preserves_original_weights(self) -> None:
        """With empty dict style data, original 4-factor weights are unchanged."""
        instructor = _make_instructor(
            teaching_style={},
            latitude=None,
            longitude=None,
        )
        job = _make_job(
            preferred_style={},
            latitude=None,
            longitude=None,
        )

        result = calculate_matching_score(instructor, job)

        assert "style" not in result["breakdown"]
        assert result["breakdown"]["region"]["weight"] == 30

    def test_only_instructor_has_style(self) -> None:
        """If only instructor has style (job does not), 4-factor weights apply."""
        instructor = _make_instructor(
            teaching_style={"correction_style": "gentle"},
            latitude=None,
            longitude=None,
        )
        job = _make_job(
            preferred_style=None,
            latitude=None,
            longitude=None,
        )

        result = calculate_matching_score(instructor, job)

        assert "style" not in result["breakdown"]
        assert result["breakdown"]["region"]["weight"] == 30

    def test_only_job_has_style(self) -> None:
        """If only job has style (instructor does not), 4-factor weights apply."""
        instructor = _make_instructor(
            teaching_style=None,
            latitude=None,
            longitude=None,
        )
        job = _make_job(
            preferred_style={"correction_style": "gentle"},
            latitude=None,
            longitude=None,
        )

        result = calculate_matching_score(instructor, job)

        assert "style" not in result["breakdown"]
        assert result["breakdown"]["region"]["weight"] == 30

    def test_distance_only_preserves_5_factor_weights(self) -> None:
        """With distance but no style, 5-factor weights unchanged."""
        instructor = _make_instructor(
            latitude=Decimal("37.4979"),
            longitude=Decimal("127.0276"),
            teaching_style=None,
        )
        job = _make_job(
            latitude=Decimal("37.4990"),
            longitude=Decimal("127.0280"),
            preferred_style=None,
        )

        result = calculate_matching_score(instructor, job)

        assert "distance" in result["breakdown"]
        assert "style" not in result["breakdown"]
        assert result["breakdown"]["distance"]["weight"] == 35
        assert result["breakdown"]["region"]["weight"] == 10


# ===========================================================================
# 5. Model column existence
# ===========================================================================

class TestStyleModelColumns:
    """Verify that style columns exist on the models."""

    def test_instructor_profile_has_teaching_style(self) -> None:
        """InstructorProfile should have teaching_style JSON column."""
        from app.models.instructor import InstructorProfile

        assert hasattr(InstructorProfile, "teaching_style")
        col = InstructorProfile.__table__.columns["teaching_style"]
        assert col.nullable is not False  # JSON columns are nullable by default

    def test_job_post_has_preferred_style(self) -> None:
        """JobPost should have preferred_style JSON column."""
        from app.models.job_post import JobPost

        assert hasattr(JobPost, "preferred_style")
        col = JobPost.__table__.columns["preferred_style"]
        assert col.nullable is not False


# ===========================================================================
# 6. Schema field existence
# ===========================================================================

class TestStyleSchemaFields:
    """Verify style fields are present in Pydantic schemas."""

    def test_job_post_create_has_preferred_style(self) -> None:
        """JobPostCreate should accept preferred_style."""
        from app.schemas.job_post import JobPostCreate

        schema = JobPostCreate(
            title="Test",
            category="pilates",
            job_type="substitute",
            date="2026-03-10",
            start_time="09:00",
            end_time="10:00",
            hourly_rate=Decimal("40000"),
            preferred_style={"correction_style": "gentle"},
            handoff_class_topic="테스트 수업",
            handoff_class_sequence_info="3주차 진도",
            handoff_atmosphere_preference="차분한",
            handoff_member_notes="없음",
            handoff_equipment_notes="기본 세팅",
        )
        assert schema.preferred_style == {"correction_style": "gentle"}

    def test_job_post_create_preferred_style_optional(self) -> None:
        """preferred_style should default to None in JobPostCreate."""
        from app.schemas.job_post import JobPostCreate

        schema = JobPostCreate(
            title="Test",
            category="pilates",
            job_type="substitute",
            date="2026-03-10",
            start_time="09:00",
            end_time="10:00",
            hourly_rate=Decimal("40000"),
            handoff_class_topic="테스트 수업",
            handoff_class_sequence_info="3주차 진도",
            handoff_atmosphere_preference="차분한",
            handoff_member_notes="없음",
            handoff_equipment_notes="기본 세팅",
        )
        assert schema.preferred_style is None

    def test_job_post_update_has_preferred_style(self) -> None:
        """JobPostUpdate should accept preferred_style."""
        from app.schemas.job_post import JobPostUpdate

        schema = JobPostUpdate(preferred_style={"intensity_level": "high"})
        assert schema.preferred_style == {"intensity_level": "high"}

    def test_job_post_response_has_preferred_style(self) -> None:
        """JobPostResponse should include preferred_style."""
        from app.schemas.job_post import JobPostResponse

        fields = JobPostResponse.model_fields
        assert "preferred_style" in fields

    def test_instructor_base_has_teaching_style(self) -> None:
        """InstructorProfileBase should accept teaching_style."""
        from app.schemas.instructor import InstructorProfileBase

        schema = InstructorProfileBase(
            display_name="Test",
            teaching_style={"correction_style": "gentle"},
        )
        assert schema.teaching_style == {"correction_style": "gentle"}

    def test_instructor_update_has_teaching_style(self) -> None:
        """InstructorProfileUpdate should accept teaching_style."""
        from app.schemas.instructor import InstructorProfileUpdate

        schema = InstructorProfileUpdate(teaching_style={"intensity_level": "low"})
        assert schema.teaching_style == {"intensity_level": "low"}

    def test_instructor_response_has_teaching_style(self) -> None:
        """InstructorProfileResponse should include teaching_style."""
        from app.schemas.instructor import InstructorProfileResponse

        fields = InstructorProfileResponse.model_fields
        assert "teaching_style" in fields

    def test_instructor_public_response_has_teaching_style(self) -> None:
        """InstructorPublicResponse should include teaching_style."""
        from app.schemas.instructor import InstructorPublicResponse

        fields = InstructorPublicResponse.model_fields
        assert "teaching_style" in fields
