from pydantic import BaseModel
from typing import Optional, List


class TierResponse(BaseModel):
    tier: str
    tier_label: str
    tier_label_ko: str
    tier_color: str
    role: str
    completed_jobs_recent: int = 0
    no_show_recent: int = 0
    same_day_cancel_recent: int = 0
    late_recent: int = 0
    cancel_after_confirm_recent: int = 0
    next_tier: Optional[str] = None
    missing_requirements: List[str] = []


class TierPublicResponse(BaseModel):
    user_id: str
    tier: str
    tier_label: str
    tier_color: str
    role: str
    completed_jobs_recent: int = 0
    no_show_recent: int = 0


class TierRequirementsResponse(BaseModel):
    teacher_tiers: List[dict]
    center_tiers: List[dict]
