from pydantic import BaseModel, Field
from typing import Optional, List
from uuid import UUID
from decimal import Decimal


class StudioProfileBase(BaseModel):
    business_name: str = Field(..., max_length=200)
    description: Optional[str] = None
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = None
    region: Optional[str] = Field(None, max_length=100)
    logo_url: Optional[str] = None
    categories: List[str] = []


class StudioProfileUpdate(BaseModel):
    business_name: Optional[str] = Field(None, max_length=200)
    description: Optional[str] = None
    phone: Optional[str] = Field(None, max_length=20)
    address: Optional[str] = None
    region: Optional[str] = Field(None, max_length=100)
    logo_url: Optional[str] = None
    categories: Optional[List[str]] = None


class StudioProfileResponse(BaseModel):
    id: UUID
    user_id: UUID
    business_name: str
    description: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    region: Optional[str] = None
    logo_url: Optional[str] = None
    categories: List[str] = []
    is_verified: bool = False
    rating_average: Decimal = Decimal("0")
    review_count: int = 0
    completed_contracts_count: int = 0  # Number of completed contracts

    class Config:
        from_attributes = True


class StudioPublicResponse(BaseModel):
    id: UUID
    business_name: str
    description: Optional[str] = None
    address: Optional[str] = None
    region: Optional[str] = None
    logo_url: Optional[str] = None
    categories: List[str] = []
    is_verified: bool = False
    rating_average: Decimal = Decimal("0")
    review_count: int = 0
    completed_contracts_count: int = 0  # Number of completed contracts

    class Config:
        from_attributes = True
