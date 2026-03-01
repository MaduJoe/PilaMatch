"""Unit tests for completed_contracts_count on instructor and studio profiles.

Verifies that:
1. InstructorService.get_completed_contracts_count returns the correct count
2. StudioService.get_completed_contracts_count returns the correct count
3. Schema responses include completed_contracts_count field
4. InstructorProfileResponse.from_model passes through completed_contracts_count
"""

import uuid
from decimal import Decimal
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.models.enums import ContractStatus
from app.schemas.instructor import (
    InstructorProfileResponse,
    InstructorPublicResponse,
)
from app.schemas.studio import (
    StudioProfileResponse,
    StudioPublicResponse,
)


# ---------------------------------------------------------------------------
# Helpers: lightweight fakes that behave like SQLAlchemy model instances
# ---------------------------------------------------------------------------

def _make_instructor_profile(
    profile_id: Optional[uuid.UUID] = None,
    user_id: Optional[uuid.UUID] = None,
    display_name: str = "Test Instructor",
    bio: Optional[str] = None,
    phone: Optional[str] = None,
    profile_image_url: Optional[str] = None,
    categories: Optional[List[str]] = None,
    specialties: Optional[List[str]] = None,
    certifications: Optional[List[Dict[str, Any]]] = None,
    experience_years: int = 3,
    hourly_rate_min: Optional[Decimal] = None,
    hourly_rate_max: Optional[Decimal] = None,
    available_regions: Optional[List[str]] = None,
    is_public: bool = True,
    rating_average: Decimal = Decimal("4.5"),
    review_count: int = 10,
) -> MagicMock:
    """Create a fake InstructorProfile model instance."""
    profile = MagicMock()
    profile.id = profile_id or uuid.uuid4()
    profile.user_id = user_id or uuid.uuid4()
    profile.display_name = display_name
    profile.bio = bio
    profile.phone = phone
    profile.profile_image_url = profile_image_url
    profile.categories = categories or ["pilates"]
    profile.specialties = specialties or ["reformer"]
    profile.certifications = certifications or []
    profile.experience_years = experience_years
    profile.hourly_rate_min = hourly_rate_min or Decimal("30000")
    profile.hourly_rate_max = hourly_rate_max or Decimal("50000")
    profile.available_regions = available_regions or ["seoul"]
    profile.is_public = is_public
    profile.teaching_style = None
    profile.rating_average = rating_average
    profile.review_count = review_count
    return profile


def _make_studio_profile(
    profile_id: Optional[uuid.UUID] = None,
    user_id: Optional[uuid.UUID] = None,
    business_name: str = "Test Studio",
    description: Optional[str] = None,
    phone: Optional[str] = None,
    address: Optional[str] = None,
    region: Optional[str] = "seoul",
    logo_url: Optional[str] = None,
    categories: Optional[List[str]] = None,
    is_verified: bool = False,
    rating_average: Decimal = Decimal("4.0"),
    review_count: int = 5,
) -> MagicMock:
    """Create a fake StudioProfile model instance."""
    profile = MagicMock()
    profile.id = profile_id or uuid.uuid4()
    profile.user_id = user_id or uuid.uuid4()
    profile.business_name = business_name
    profile.description = description
    profile.phone = phone
    profile.address = address
    profile.region = region
    profile.logo_url = logo_url
    profile.categories = categories or ["pilates"]
    profile.is_verified = is_verified
    profile.rating_average = rating_average
    profile.review_count = review_count
    return profile


# ---------------------------------------------------------------------------
# InstructorProfileResponse.from_model tests
# ---------------------------------------------------------------------------

class TestInstructorProfileResponseFromModel:
    """Tests for InstructorProfileResponse.from_model with completed_contracts_count."""

    def test_from_model_default_zero(self) -> None:
        """completed_contracts_count defaults to 0 when not provided."""
        profile = _make_instructor_profile()
        response = InstructorProfileResponse.from_model(profile)
        assert response.completed_contracts_count == 0

    def test_from_model_with_count(self) -> None:
        """completed_contracts_count is correctly passed through from_model."""
        profile = _make_instructor_profile()
        response = InstructorProfileResponse.from_model(
            profile, completed_contracts_count=15
        )
        assert response.completed_contracts_count == 15

    def test_from_model_preserves_other_fields(self) -> None:
        """Other fields are not affected by adding completed_contracts_count."""
        profile = _make_instructor_profile(
            display_name="Alice",
            experience_years=5,
            rating_average=Decimal("4.8"),
            review_count=20,
        )
        response = InstructorProfileResponse.from_model(
            profile, completed_contracts_count=7
        )
        assert response.display_name == "Alice"
        assert response.experience_years == 5
        assert response.rating_average == Decimal("4.8")
        assert response.review_count == 20
        assert response.completed_contracts_count == 7

    def test_from_model_with_verified_certifications(self) -> None:
        """verified_cert_count and completed_contracts_count coexist correctly."""
        certs = [
            {"name": "PMA", "is_verified": True},
            {"name": "STOTT", "is_verified": False},
            {"name": "Balanced Body", "is_verified": True},
        ]
        profile = _make_instructor_profile(certifications=certs)
        response = InstructorProfileResponse.from_model(
            profile, completed_contracts_count=3
        )
        assert response.verified_cert_count == 2
        assert response.completed_contracts_count == 3


# ---------------------------------------------------------------------------
# InstructorPublicResponse schema tests
# ---------------------------------------------------------------------------

class TestInstructorPublicResponseSchema:
    """Tests for InstructorPublicResponse schema with completed_contracts_count."""

    def test_field_exists_with_default_zero(self) -> None:
        """Schema declares completed_contracts_count with default 0."""
        # Construct directly to verify the default
        response = InstructorPublicResponse(
            id=uuid.uuid4(),
            display_name="Test",
        )
        assert response.completed_contracts_count == 0

    def test_field_can_be_set_after_validate(self) -> None:
        """completed_contracts_count can be set after model_validate."""
        profile = _make_instructor_profile()
        response = InstructorPublicResponse.model_validate(profile)
        response.completed_contracts_count = 42
        assert response.completed_contracts_count == 42

    def test_field_included_in_serialization(self) -> None:
        """completed_contracts_count appears in serialized output."""
        response = InstructorPublicResponse(
            id=uuid.uuid4(),
            display_name="Test",
            completed_contracts_count=5,
        )
        data = response.model_dump()
        assert "completed_contracts_count" in data
        assert data["completed_contracts_count"] == 5


# ---------------------------------------------------------------------------
# StudioProfileResponse schema tests
# ---------------------------------------------------------------------------

class TestStudioProfileResponseSchema:
    """Tests for StudioProfileResponse schema with completed_contracts_count."""

    def test_field_exists_with_default_zero(self) -> None:
        """Schema declares completed_contracts_count with default 0."""
        response = StudioProfileResponse(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            business_name="Test Studio",
        )
        assert response.completed_contracts_count == 0

    def test_field_can_be_set_after_validate(self) -> None:
        """completed_contracts_count can be set after model_validate."""
        profile = _make_studio_profile()
        response = StudioProfileResponse.model_validate(profile)
        response.completed_contracts_count = 25
        assert response.completed_contracts_count == 25

    def test_field_included_in_serialization(self) -> None:
        """completed_contracts_count appears in serialized output."""
        response = StudioProfileResponse(
            id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            business_name="Test Studio",
            completed_contracts_count=8,
        )
        data = response.model_dump()
        assert "completed_contracts_count" in data
        assert data["completed_contracts_count"] == 8


# ---------------------------------------------------------------------------
# StudioPublicResponse schema tests
# ---------------------------------------------------------------------------

class TestStudioPublicResponseSchema:
    """Tests for StudioPublicResponse schema with completed_contracts_count."""

    def test_field_exists_with_default_zero(self) -> None:
        """Schema declares completed_contracts_count with default 0."""
        response = StudioPublicResponse(
            id=uuid.uuid4(),
            business_name="Test Studio",
        )
        assert response.completed_contracts_count == 0

    def test_field_can_be_set_after_validate(self) -> None:
        """completed_contracts_count can be set after model_validate."""
        profile = _make_studio_profile()
        response = StudioPublicResponse.model_validate(profile)
        response.completed_contracts_count = 10
        assert response.completed_contracts_count == 10

    def test_field_included_in_serialization(self) -> None:
        """completed_contracts_count appears in serialized output."""
        response = StudioPublicResponse(
            id=uuid.uuid4(),
            business_name="Test Studio",
            completed_contracts_count=3,
        )
        data = response.model_dump()
        assert "completed_contracts_count" in data
        assert data["completed_contracts_count"] == 3


# ---------------------------------------------------------------------------
# InstructorService.get_completed_contracts_count tests
# ---------------------------------------------------------------------------

class TestInstructorServiceCompletedCount:
    """Tests for InstructorService.get_completed_contracts_count."""

    @pytest.mark.asyncio
    async def test_returns_zero_when_no_contracts(self) -> None:
        """Returns 0 when instructor has no completed contracts."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = 0
        mock_db.execute.return_value = mock_result

        from app.services.instructor import InstructorService
        service = InstructorService(mock_db)
        count = await service.get_completed_contracts_count(uuid.uuid4())

        assert count == 0
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_correct_count(self) -> None:
        """Returns correct count when instructor has completed contracts."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = 7
        mock_db.execute.return_value = mock_result

        from app.services.instructor import InstructorService
        service = InstructorService(mock_db)
        count = await service.get_completed_contracts_count(uuid.uuid4())

        assert count == 7

    @pytest.mark.asyncio
    async def test_returns_zero_when_scalar_is_none(self) -> None:
        """Returns 0 when scalar result is None (no matching rows)."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = None
        mock_db.execute.return_value = mock_result

        from app.services.instructor import InstructorService
        service = InstructorService(mock_db)
        count = await service.get_completed_contracts_count(uuid.uuid4())

        assert count == 0


# ---------------------------------------------------------------------------
# StudioService.get_completed_contracts_count tests
# ---------------------------------------------------------------------------

class TestStudioServiceCompletedCount:
    """Tests for StudioService.get_completed_contracts_count."""

    @pytest.mark.asyncio
    async def test_returns_zero_when_no_contracts(self) -> None:
        """Returns 0 when studio has no completed contracts."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = 0
        mock_db.execute.return_value = mock_result

        from app.services.studio import StudioService
        service = StudioService(mock_db)
        count = await service.get_completed_contracts_count(uuid.uuid4())

        assert count == 0
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_returns_correct_count(self) -> None:
        """Returns correct count when studio has completed contracts."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = 12
        mock_db.execute.return_value = mock_result

        from app.services.studio import StudioService
        service = StudioService(mock_db)
        count = await service.get_completed_contracts_count(uuid.uuid4())

        assert count == 12

    @pytest.mark.asyncio
    async def test_returns_zero_when_scalar_is_none(self) -> None:
        """Returns 0 when scalar result is None (no matching rows)."""
        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar.return_value = None
        mock_db.execute.return_value = mock_result

        from app.services.studio import StudioService
        service = StudioService(mock_db)
        count = await service.get_completed_contracts_count(uuid.uuid4())

        assert count == 0


# ---------------------------------------------------------------------------
# Contract status value consistency test
# ---------------------------------------------------------------------------

class TestContractStatusValue:
    """Verify that ContractStatus.COMPLETED.value matches the expected string."""

    def test_completed_status_value(self) -> None:
        """ContractStatus.COMPLETED.value should be 'completed'."""
        assert ContractStatus.COMPLETED.value == "completed"
