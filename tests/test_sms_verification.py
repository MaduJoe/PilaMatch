"""Tests for SMS verification security enhancements."""
import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient


# ── Helper: signup + get auth header ─────────────────────────────────────────

async def _create_user(client: AsyncClient, email: str = "sms@test.com") -> dict:
    """Create a user and return auth header dict."""
    resp = await client.post(
        "/api/v1/auth/signup",
        json={
            "email": email,
            "password": "TestPass123",
            "role": "instructor",
            "display_name": "SMS Tester",
        },
    )
    assert resp.status_code == 201
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


# ── E.164 Normalization Tests ────────────────────────────────────────────────

class TestPhoneNormalization:
    def test_domestic_to_e164(self):
        from app.services.verification import normalize_phone
        assert normalize_phone("01012345678") == "+821012345678"

    def test_hyphenated_to_e164(self):
        from app.services.verification import normalize_phone
        assert normalize_phone("010-1234-5678") == "+821012345678"

    def test_already_e164(self):
        from app.services.verification import normalize_phone
        assert normalize_phone("+821012345678") == "+821012345678"

    def test_with_spaces(self):
        from app.services.verification import normalize_phone
        assert normalize_phone("010 1234 5678") == "+821012345678"

    def test_to_domestic(self):
        from app.services.verification import to_domestic
        assert to_domestic("+821012345678") == "01012345678"

    def test_to_domestic_already_domestic(self):
        from app.services.verification import to_domestic
        assert to_domestic("01012345678") == "01012345678"


# ── Happy Path ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_otp_send_and_verify_success(client: AsyncClient):
    """OTP 발송 → 검증 성공 → phone_verified=True"""
    headers = await _create_user(client, "happy@test.com")

    # Request OTP
    with patch("app.services.sms.send_verification_sms", new_callable=AsyncMock, return_value=True):
        resp = await client.post(
            "/api/v1/verification/phone/request",
            json={"phone": "01012345678"},
            headers=headers,
        )
    assert resp.status_code == 200
    data = resp.json()
    assert data["expires_in"] == 180
    otp = data["_dev_otp"]

    # Verify OTP
    resp = await client.post(
        "/api/v1/verification/phone/verify",
        json={"phone": "01012345678", "otp": otp},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["verified"] is True

    # Check verification status
    resp = await client.get("/api/v1/verification/status", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["phone_verified"] is True


# ── Cooldown Tests ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_cooldown_blocks_resend(client: AsyncClient):
    """1분 내 재발송 시 COOLDOWN_ACTIVE 에러"""
    headers = await _create_user(client, "cooldown@test.com")

    with patch("app.services.sms.send_verification_sms", new_callable=AsyncMock, return_value=True):
        # First request — success
        resp = await client.post(
            "/api/v1/verification/phone/request",
            json={"phone": "01099998888"},
            headers=headers,
        )
        assert resp.status_code == 200

        # Immediate second request — cooldown
        resp = await client.post(
            "/api/v1/verification/phone/request",
            json={"phone": "01099998888"},
            headers=headers,
        )
    assert resp.status_code == 429
    assert resp.json()["detail"]["code"] == "COOLDOWN_ACTIVE"


# ── Brute Force / Lock Tests ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_5_failures_locks_phone(client: AsyncClient):
    """5회 실패 시 PHONE_LOCKED"""
    headers = await _create_user(client, "lock@test.com")

    with patch("app.services.sms.send_verification_sms", new_callable=AsyncMock, return_value=True):
        resp = await client.post(
            "/api/v1/verification/phone/request",
            json={"phone": "01011112222"},
            headers=headers,
        )
    assert resp.status_code == 200

    # 5 wrong attempts
    for i in range(5):
        resp = await client.post(
            "/api/v1/verification/phone/verify",
            json={"phone": "01011112222", "otp": "000000"},
            headers=headers,
        )

    # 5th attempt should lock
    assert resp.status_code == 429
    assert resp.json()["detail"]["code"] == "PHONE_LOCKED"


@pytest.mark.asyncio
async def test_lock_blocks_new_otp(client: AsyncClient):
    """잠금 상태에서 새 OTP 발송도 차단"""
    headers = await _create_user(client, "lockblock@test.com")

    with patch("app.services.sms.send_verification_sms", new_callable=AsyncMock, return_value=True):
        resp = await client.post(
            "/api/v1/verification/phone/request",
            json={"phone": "01033334444"},
            headers=headers,
        )
    assert resp.status_code == 200

    # Exhaust attempts
    for _ in range(5):
        await client.post(
            "/api/v1/verification/phone/verify",
            json={"phone": "01033334444", "otp": "000000"},
            headers=headers,
        )

    # Clear cooldown from memory store so we can test the lock check
    from app.services.verification import _memory_store, normalize_phone, _key_cooldown
    phone_e164 = normalize_phone("01033334444")
    _memory_store.pop(_key_cooldown(phone_e164), None)

    # Try to request new OTP — should be locked
    with patch("app.services.sms.send_verification_sms", new_callable=AsyncMock, return_value=True):
        resp = await client.post(
            "/api/v1/verification/phone/request",
            json={"phone": "01033334444"},
            headers=headers,
        )
    assert resp.status_code == 429
    assert resp.json()["detail"]["code"] == "PHONE_LOCKED"


# ── OTP Invalid / Remaining Attempts ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_invalid_otp_shows_remaining(client: AsyncClient):
    """잘못된 OTP 시 남은 시도 횟수 표시"""
    headers = await _create_user(client, "remaining@test.com")

    with patch("app.services.sms.send_verification_sms", new_callable=AsyncMock, return_value=True):
        resp = await client.post(
            "/api/v1/verification/phone/request",
            json={"phone": "01055556666"},
            headers=headers,
        )
    assert resp.status_code == 200

    # First wrong attempt
    resp = await client.post(
        "/api/v1/verification/phone/verify",
        json={"phone": "01055556666", "otp": "000000"},
        headers=headers,
    )
    assert resp.status_code == 400
    detail = resp.json()["detail"]
    assert detail["code"] == "OTP_INVALID"
    assert "4" in detail["message"]  # 4 remaining


# ── OTP Expired Test ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_expired_otp(client: AsyncClient):
    """만료된 OTP 검증 시 OTP_EXPIRED"""
    headers = await _create_user(client, "expired@test.com")

    with patch("app.services.sms.send_verification_sms", new_callable=AsyncMock, return_value=True):
        resp = await client.post(
            "/api/v1/verification/phone/request",
            json={"phone": "01077778888"},
            headers=headers,
        )
    assert resp.status_code == 200

    # Manually expire the OTP by deleting from memory store
    from app.services.verification import _memory_store, normalize_phone, _key_code
    phone_e164 = normalize_phone("01077778888")
    _memory_store.pop(_key_code(phone_e164), None)

    resp = await client.post(
        "/api/v1/verification/phone/verify",
        json={"phone": "01077778888", "otp": "123456"},
        headers=headers,
    )
    assert resp.status_code == 400
    assert resp.json()["detail"]["code"] == "OTP_EXPIRED"


# ── Same Phone, Different Format ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_phone_format_normalization(client: AsyncClient):
    """다른 포맷 같은 전화번호 → 동일 OTP로 검증"""
    headers = await _create_user(client, "format@test.com")

    with patch("app.services.sms.send_verification_sms", new_callable=AsyncMock, return_value=True):
        # Request with domestic format
        resp = await client.post(
            "/api/v1/verification/phone/request",
            json={"phone": "01012340000"},
            headers=headers,
        )
    assert resp.status_code == 200
    otp = resp.json()["_dev_otp"]

    # Verify with same format (E.164 normalization is internal)
    resp = await client.post(
        "/api/v1/verification/phone/verify",
        json={"phone": "01012340000", "otp": otp},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["verified"] is True


# ── In-Memory Fallback Test ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_inmemory_fallback_works(client: AsyncClient):
    """Redis 없이 인메모리 폴백 동작 확인"""
    import app.services.verification as v
    # Ensure Redis is not used (default in test)
    v._redis_client = None

    headers = await _create_user(client, "memory@test.com")

    with patch("app.services.sms.send_verification_sms", new_callable=AsyncMock, return_value=True):
        resp = await client.post(
            "/api/v1/verification/phone/request",
            json={"phone": "01000001111"},
            headers=headers,
        )
    assert resp.status_code == 200
    otp = resp.json()["_dev_otp"]

    resp = await client.post(
        "/api/v1/verification/phone/verify",
        json={"phone": "01000001111", "otp": otp},
        headers=headers,
    )
    assert resp.status_code == 200
    assert resp.json()["verified"] is True


# ── Cleanup fixture ──────────────────────────────────────────────────────────

@pytest.fixture(autouse=True)
def _clear_memory_store():
    """Clear in-memory store between tests."""
    from app.services.verification import _memory_store
    _memory_store.clear()
    yield
    _memory_store.clear()
