from pydantic import BaseModel, Field
from typing import Optional, List, Union
from uuid import UUID
from decimal import Decimal


class Certification(BaseModel):
    """Certification with verification status."""
    name: str
    issuer: Optional[str] = None
    year: Optional[int] = None
    is_verified: bool = False


class InstructorProfileBase(BaseModel):
    display_name: str = Field(..., max_length=100)
    bio: Optional[str] = None
    phone: Optional[str] = Field(None, max_length=20)
    profile_image_url: Optional[str] = None
    categories: List[str] = []
    specialties: List[str] = []
    certifications: List[Union[Certification, str]] = []  # Support both formats
    experience_years: int = 0
    hourly_rate_min: Optional[Decimal] = None
    hourly_rate_max: Optional[Decimal] = None
    available_regions: List[str] = []
    is_public: bool = True
    teaching_style: Optional[dict] = None  # {correction_style, class_atmosphere, intensity_level, music_preference}


class InstructorProfileUpdate(BaseModel):
    display_name: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = None
    phone: Optional[str] = Field(None, max_length=20)
    profile_image_url: Optional[str] = None
    categories: Optional[List[str]] = None
    specialties: Optional[List[str]] = None
    certifications: Optional[List[Union[Certification, str]]] = None
    experience_years: Optional[int] = None
    hourly_rate_min: Optional[Decimal] = None
    hourly_rate_max: Optional[Decimal] = None
    available_regions: Optional[List[str]] = None
    is_public: Optional[bool] = None
    teaching_style: Optional[dict] = None


class InstructorProfileResponse(BaseModel):
    id: UUID
    user_id: UUID
    display_name: str
    bio: Optional[str] = None
    phone: Optional[str] = None
    profile_image_url: Optional[str] = None
    categories: List[str] = []
    specialties: List[str] = []
    certifications: List[Union[Certification, dict, str]] = []
    experience_years: int = 0
    hourly_rate_min: Optional[Decimal] = None
    hourly_rate_max: Optional[Decimal] = None
    available_regions: List[str] = []
    is_public: bool = True
    teaching_style: Optional[dict] = None
    rating_average: Decimal = Decimal("0")
    review_count: int = 0
    verified_cert_count: int = 0  # Number of verified certifications
    completed_contracts_count: int = 0  # Number of completed contracts

    class Config:
        from_attributes = True

    @classmethod
    def from_model(cls, profile, completed_contracts_count: int = 0):
        """Create response from model with computed fields.

        Args:
            profile: InstructorProfile model instance.
            completed_contracts_count: Number of completed contracts for this instructor.
        """
        certs = profile.certifications or []
        verified_count = sum(
            1 for c in certs
            if isinstance(c, dict) and c.get("is_verified", False)
        )

        return cls(
            id=profile.id,
            user_id=profile.user_id,
            display_name=profile.display_name,
            bio=profile.bio,
            phone=profile.phone,
            profile_image_url=profile.profile_image_url,
            categories=profile.categories or [],
            specialties=profile.specialties or [],
            certifications=certs,
            experience_years=profile.experience_years or 0,
            hourly_rate_min=profile.hourly_rate_min,
            hourly_rate_max=profile.hourly_rate_max,
            available_regions=profile.available_regions or [],
            is_public=profile.is_public,
            teaching_style=profile.teaching_style if hasattr(profile, 'teaching_style') else None,
            rating_average=profile.rating_average or Decimal("0"),
            review_count=profile.review_count or 0,
            verified_cert_count=verified_count,
            completed_contracts_count=completed_contracts_count,
        )


class InstructorPublicResponse(BaseModel):
    id: UUID
    display_name: str
    bio: Optional[str] = None
    profile_image_url: Optional[str] = None
    categories: List[str] = []
    specialties: List[str] = []
    certifications: List[Union[Certification, dict, str]] = []
    experience_years: int = 0
    hourly_rate_min: Optional[Decimal] = None
    hourly_rate_max: Optional[Decimal] = None
    available_regions: List[str] = []
    teaching_style: Optional[dict] = None
    rating_average: Decimal = Decimal("0")
    review_count: int = 0
    verified_cert_count: int = 0
    completed_contracts_count: int = 0  # Number of completed contracts

    class Config:
        from_attributes = True
