"""Kakao Local API proxy — address/keyword search for autocomplete."""

import logging
from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel

from app.core.config import settings
from app.core.deps import get_current_user
from app.models import User

logger = logging.getLogger(__name__)
router = APIRouter()


class KakaoPlaceResult(BaseModel):
    place_name: str
    address_name: str
    road_address_name: str
    region: str
    latitude: float
    longitude: float
    phone: str


class KakaoSearchResponse(BaseModel):
    results: list[KakaoPlaceResult]
    total: int


@router.get("/search", response_model=KakaoSearchResponse)
async def search_kakao_places(
    query: str = Query(..., min_length=2, max_length=100),
    page: int = Query(1, ge=1, le=3),
    current_user: User = Depends(get_current_user),
):
    """Search places via Kakao Local keyword API (backend proxy)."""
    api_key = settings.KAKAO_REST_API_KEY
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="카카오 API 키가 설정되지 않았습니다.",
        )

    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    headers = {"Authorization": f"KakaoAK {api_key}"}
    params = {
        "query": query,
        "size": 10,
        "page": page,
    }

    try:
        async with httpx.AsyncClient(timeout=5) as client:
            res = await client.get(url, headers=headers, params=params)

        if res.status_code != 200:
            logger.warning(f"Kakao API error: {res.status_code} {res.text}")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="카카오 API 호출에 실패했습니다.",
            )

        data = res.json()
        documents = data.get("documents", [])
        total = data.get("meta", {}).get("total_count", 0)

        results = []
        for doc in documents:
            # Extract gu/구 from address for region field
            addr = doc.get("address_name", "")
            parts = addr.split()
            region = parts[1] if len(parts) >= 2 else ""

            results.append(
                KakaoPlaceResult(
                    place_name=doc.get("place_name", ""),
                    address_name=addr,
                    road_address_name=doc.get("road_address_name", "") or addr,
                    region=region,
                    latitude=float(doc.get("y", 0)),
                    longitude=float(doc.get("x", 0)),
                    phone=doc.get("phone", ""),
                )
            )

        return KakaoSearchResponse(results=results, total=total)

    except httpx.RequestError as e:
        logger.error(f"Kakao API request failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="카카오 API 연결에 실패했습니다.",
        )
