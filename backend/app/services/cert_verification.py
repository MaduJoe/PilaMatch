"""Certificate verification using Claude Vision API."""

import base64
import json
import logging
from dataclasses import dataclass
from typing import Optional

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

VERIFICATION_PROMPT = """이 이미지가 필라테스/요가 관련 자격증 또는 인증서류인지 검증해주세요.

확인 항목:
1. 발급기관명 (예: 대한체육회, KACEP, PMA, 대한필라테스협회, 요가협회, 체육지도자 등)
2. 자격증/인증서 명칭
3. 발급일자 (있으면)
4. 성명 (있으면)

다음 JSON 형식으로만 응답하세요 (다른 텍스트 없이):
{"is_valid": true/false, "cert_name": "자격증명", "issuer": "발급기관", "confidence": 0.0~1.0, "reason": "판단 근거"}

판단 기준:
- 필라테스/요가/체육/운동 관련 자격증이면 is_valid: true
- 관련 없는 문서, 불분명한 이미지, 텍스트 없는 이미지는 is_valid: false
- confidence: 0.8 이상이면 자동 승인, 미만이면 수동 검토 필요"""


@dataclass
class CertVerificationResult:
    is_valid: bool
    cert_name: str
    issuer: str
    confidence: float
    reason: str
    auto_approved: bool  # confidence >= 0.8


async def verify_certification_image(image_bytes: bytes) -> CertVerificationResult:
    """Verify a certification image using Claude Vision API.

    Args:
        image_bytes: Resized image bytes (max 1568px).

    Returns:
        CertVerificationResult with verification details.
    """
    if not settings.ANTHROPIC_API_KEY:
        logger.warning("ANTHROPIC_API_KEY not set, auto-approving in dev mode")
        return CertVerificationResult(
            is_valid=True,
            cert_name="자격증 (개발모드 자동승인)",
            issuer="개발모드",
            confidence=1.0,
            reason="ANTHROPIC_API_KEY 미설정 — 개발모드 자동승인",
            auto_approved=True,
        )

    image_b64 = base64.standard_b64encode(image_bytes).decode("utf-8")

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": settings.ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-sonnet-4-6-20250514",
                    "max_tokens": 512,
                    "messages": [
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image",
                                    "source": {
                                        "type": "base64",
                                        "media_type": "image/jpeg",
                                        "data": image_b64,
                                    },
                                },
                                {
                                    "type": "text",
                                    "text": VERIFICATION_PROMPT,
                                },
                            ],
                        }
                    ],
                },
            )

        if response.status_code != 200:
            logger.error(f"Claude API error: {response.status_code} {response.text}")
            return _fallback_result("Claude API 호출 실패")

        data = response.json()
        text = data["content"][0]["text"].strip()

        # Parse JSON from response (handle markdown code blocks)
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()

        result = json.loads(text)
        auto_approved = result.get("is_valid", False) and result.get("confidence", 0) >= 0.8

        logger.info(
            f"Cert verification: valid={result.get('is_valid')} "
            f"confidence={result.get('confidence')} auto_approved={auto_approved}"
        )

        return CertVerificationResult(
            is_valid=result.get("is_valid", False),
            cert_name=result.get("cert_name", ""),
            issuer=result.get("issuer", ""),
            confidence=result.get("confidence", 0.0),
            reason=result.get("reason", ""),
            auto_approved=auto_approved,
        )

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Claude response: {e}")
        return _fallback_result("응답 파싱 실패")
    except Exception as e:
        logger.error(f"Cert verification error: {e}")
        return _fallback_result(str(e))


def _fallback_result(reason: str) -> CertVerificationResult:
    """Return a pending-review result when verification fails."""
    return CertVerificationResult(
        is_valid=False,
        cert_name="",
        issuer="",
        confidence=0.0,
        reason=f"자동 검증 실패: {reason}. 수동 검토가 필요합니다.",
        auto_approved=False,
    )
