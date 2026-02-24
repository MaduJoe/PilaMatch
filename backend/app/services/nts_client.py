"""국세청 사업자등록정보 조회 API client."""

import logging
from dataclasses import dataclass
from typing import Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class NTSBusinessStatus:
    """Result from NTS business status check."""
    is_operating: bool        # b_stt_cd == "01"
    status_code: str          # e.g. "01"
    status_label: str         # e.g. "계속사업자"
    tax_type: Optional[str]   # e.g. "일반과세자"
    tax_type_label: Optional[str]


def validate_business_number_checksum(b_no: str) -> bool:
    """Validate Korean business registration number checksum.

    Format: 10 digits (XXX-XX-XXXXX without hyphens).
    Algorithm uses weighted sum with specific multipliers.
    """
    if len(b_no) != 10 or not b_no.isdigit():
        return False

    weights = [1, 3, 7, 1, 3, 7, 1, 3, 5]
    total = sum(int(b_no[i]) * weights[i] for i in range(9))
    total += (int(b_no[8]) * 5) // 10
    check = (10 - (total % 10)) % 10
    return check == int(b_no[9])


async def check_business_status_dev(b_no: str) -> NTSBusinessStatus:
    """Dev mode: validate using checksum algorithm only."""
    clean = b_no.replace("-", "")
    if validate_business_number_checksum(clean):
        return NTSBusinessStatus(
            is_operating=True,
            status_code="01",
            status_label="계속사업자 (개발모드)",
            tax_type="일반과세자",
            tax_type_label="일반과세자 (개발모드)",
        )
    return NTSBusinessStatus(
        is_operating=False,
        status_code="00",
        status_label="유효하지 않은 사업자번호 (체크섬 실패)",
        tax_type=None,
        tax_type_label=None,
    )


async def check_business_status(b_no: str) -> NTSBusinessStatus:
    """Check business status via 국세청 API (or dev mock).

    Args:
        b_no: Business registration number (10 digits, no hyphens).
    """
    clean = b_no.replace("-", "")

    # Dev mode: use checksum validation only
    if not settings.NTS_SERVICE_KEY:
        logger.info(f"NTS_SERVICE_KEY not set, using dev checksum for {clean}")
        return await check_business_status_dev(clean)

    # Production: call 국세청 API
    try:
        url = f"{settings.NTS_API_BASE_URL}/status"
        params = {"serviceKey": settings.NTS_SERVICE_KEY}
        body = {"b_no": [clean]}

        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(url, params=params, json=body)

        if response.status_code != 200:
            logger.error(f"NTS API error: {response.status_code} {response.text}")
            # Fallback to checksum
            return await check_business_status_dev(clean)

        data = response.json()
        items = data.get("data", [])
        if not items:
            return NTSBusinessStatus(
                is_operating=False,
                status_code="00",
                status_label="조회 결과 없음",
                tax_type=None,
                tax_type_label=None,
            )

        item = items[0]
        b_stt_cd = item.get("b_stt_cd", "")
        b_stt = item.get("b_stt", "알 수 없음")
        tax_type = item.get("tax_type", "")
        tax_type_cd = item.get("tax_type_cd", "")

        return NTSBusinessStatus(
            is_operating=(b_stt_cd == "01"),
            status_code=b_stt_cd,
            status_label=b_stt,
            tax_type=tax_type_cd,
            tax_type_label=tax_type,
        )

    except Exception as e:
        logger.error(f"NTS API exception: {e}")
        # Fallback to checksum
        return await check_business_status_dev(clean)
