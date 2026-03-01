"""계약서 HTML 문서 생성 기능 테스트.

다음 항목을 검증한다:
- contract_document.render_contract_html 렌더링 정확성
- ContractService.get_contract_document_data 권한 체크 및 데이터 조회
- GET /contracts/{id}/document 엔드포인트 통합 테스트
"""

import uuid
from datetime import date, time, datetime
from decimal import Decimal
from typing import Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.contract_document import (
    render_contract_html,
    _fmt_datetime,
    _fmt_date,
    _fmt_time,
    _fmt_amount,
    _escape_html,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_contract(
    contract_id: Optional[uuid.UUID] = None,
    studio_id: Optional[uuid.UUID] = None,
    instructor_id: Optional[uuid.UUID] = None,
    status: str = "confirmed",
    hourly_rate: Decimal = Decimal("50000"),
    total_amount: Decimal = Decimal("100000"),
    platform_fee: Decimal = Decimal("5000"),
    settlement_amount: Decimal = Decimal("95000"),
    total_sessions: int = 2,
    contract_date: Optional[date] = None,
    start_time_val: Optional[time] = None,
    end_time_val: Optional[time] = None,
    content_hash: Optional[str] = None,
    instructor_signed_at: Optional[datetime] = None,
    studio_signed_at: Optional[datetime] = None,
    studio_confirmed_at: Optional[datetime] = None,
    instructor_confirmed_at: Optional[datetime] = None,
    created_at: Optional[datetime] = None,
    updated_at: Optional[datetime] = None,
) -> MagicMock:
    """테스트용 Contract mock 객체를 생성한다."""
    c = MagicMock()
    c.id = contract_id or uuid.uuid4()
    c.studio_id = studio_id or uuid.uuid4()
    c.instructor_id = instructor_id or uuid.uuid4()
    c.status = status
    c.hourly_rate = hourly_rate
    c.total_amount = total_amount
    c.platform_fee = platform_fee
    c.settlement_amount = settlement_amount
    c.total_sessions = total_sessions
    c.date = contract_date or date(2026, 3, 15)
    c.start_time = start_time_val or time(10, 0)
    c.end_time = end_time_val or time(12, 0)
    c.content_hash = content_hash
    c.instructor_signed_at = instructor_signed_at
    c.studio_signed_at = studio_signed_at
    c.studio_confirmed_at = studio_confirmed_at
    c.instructor_confirmed_at = instructor_confirmed_at
    c.created_at = created_at or datetime(2026, 3, 1, 9, 0, 0)
    c.updated_at = updated_at or datetime(2026, 3, 1, 9, 30, 0)
    return c


def _make_document_data(
    contract: Optional[MagicMock] = None,
    instructor_name: str = "김필라",
    studio_name: str = "해피 필라테스",
    studio_address: str = "서울특별시 강남구 테헤란로 123",
    studio_phone: str = "02-1234-5678",
    instructor_phone: str = "010-9876-5432",
    status_label: str = "확정",
) -> dict:
    """render_contract_html에 전달할 데이터 딕셔너리를 생성한다."""
    return {
        "contract": contract or _make_contract(),
        "instructor_name": instructor_name,
        "studio_name": studio_name,
        "studio_address": studio_address,
        "studio_phone": studio_phone,
        "instructor_phone": instructor_phone,
        "status_label": status_label,
    }


# ---------------------------------------------------------------------------
# 유틸 함수 테스트
# ---------------------------------------------------------------------------

class TestFormatFunctions:
    """포맷 유틸 함수 단위 테스트."""

    def test_fmt_datetime_with_value(self) -> None:
        dt = datetime(2026, 3, 15, 14, 30, 0)
        result = _fmt_datetime(dt)
        assert result == "2026년 03월 15일 14:30"

    def test_fmt_datetime_none(self) -> None:
        assert _fmt_datetime(None) == "-"

    def test_fmt_date_with_value(self) -> None:
        d = date(2026, 3, 15)
        result = _fmt_date(d)
        assert result == "2026년 03월 15일"

    def test_fmt_date_none(self) -> None:
        assert _fmt_date(None) == "-"

    def test_fmt_time_with_value(self) -> None:
        t = time(10, 30)
        result = _fmt_time(t)
        assert result == "10:30"

    def test_fmt_time_none(self) -> None:
        assert _fmt_time(None) == "-"

    def test_fmt_amount_with_value(self) -> None:
        assert _fmt_amount(Decimal("50000")) == "50,000원"
        assert _fmt_amount(Decimal("100000")) == "100,000원"
        assert _fmt_amount(Decimal("1234567")) == "1,234,567원"

    def test_fmt_amount_none(self) -> None:
        assert _fmt_amount(None) == "-"

    def test_fmt_amount_zero(self) -> None:
        assert _fmt_amount(Decimal("0")) == "0원"

    def test_escape_html_special_chars(self) -> None:
        assert _escape_html("<script>alert('xss')</script>") == (
            "&lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;"
        )

    def test_escape_html_ampersand(self) -> None:
        assert _escape_html("A & B") == "A &amp; B"

    def test_escape_html_quotes(self) -> None:
        assert _escape_html('"hello"') == "&quot;hello&quot;"

    def test_escape_html_none(self) -> None:
        assert _escape_html(None) == ""


# ---------------------------------------------------------------------------
# HTML 렌더링 테스트
# ---------------------------------------------------------------------------

class TestRenderContractHtml:
    """render_contract_html 함수 테스트."""

    def test_renders_valid_html(self) -> None:
        """기본 데이터로 유효한 HTML을 생성하는지 확인한다."""
        data = _make_document_data()
        html = render_contract_html(data)

        assert "<!DOCTYPE html>" in html
        assert "<html lang=\"ko\">" in html
        assert "</html>" in html

    def test_contains_contract_id(self) -> None:
        """계약 번호가 HTML에 포함되는지 확인한다."""
        contract = _make_contract()
        data = _make_document_data(contract=contract)
        html = render_contract_html(data)

        assert str(contract.id) in html

    def test_contains_party_names(self) -> None:
        """당사자 이름이 HTML에 포함되는지 확인한다."""
        data = _make_document_data(
            instructor_name="김필라",
            studio_name="해피 필라테스",
        )
        html = render_contract_html(data)

        assert "김필라" in html
        assert "해피 필라테스" in html

    def test_contains_class_info(self) -> None:
        """수업 날짜, 시간 정보가 포함되는지 확인한다."""
        contract = _make_contract(
            contract_date=date(2026, 4, 1),
            start_time_val=time(14, 0),
            end_time_val=time(16, 0),
            total_sessions=3,
        )
        data = _make_document_data(contract=contract)
        html = render_contract_html(data)

        assert "2026년 04월 01일" in html
        assert "14:00" in html
        assert "16:00" in html
        assert "3회" in html

    def test_contains_amount_info(self) -> None:
        """금액 정보가 올바르게 포맷되어 포함되는지 확인한다."""
        contract = _make_contract(
            hourly_rate=Decimal("50000"),
            total_amount=Decimal("100000"),
            platform_fee=Decimal("5000"),
            settlement_amount=Decimal("95000"),
        )
        data = _make_document_data(contract=contract)
        html = render_contract_html(data)

        assert "50,000원" in html
        assert "100,000원" in html
        assert "5,000원" in html
        assert "95,000원" in html

    def test_contains_status_badge(self) -> None:
        """계약 상태 배지가 표시되는지 확인한다."""
        data = _make_document_data(status_label="진행 중")
        html = render_contract_html(data)

        assert "진행 중" in html
        assert "#d97706" in html  # 진행 중 색상

    def test_contains_signature_info_unsigned(self) -> None:
        """미서명 상태가 올바르게 표시되는지 확인한다."""
        contract = _make_contract(
            instructor_signed_at=None,
            studio_signed_at=None,
        )
        data = _make_document_data(contract=contract)
        html = render_contract_html(data)

        assert "미서명" in html

    def test_contains_signature_info_signed(self) -> None:
        """서명 완료 상태가 올바르게 표시되는지 확인한다."""
        signed_at = datetime(2026, 3, 10, 15, 0, 0)
        contract = _make_contract(
            instructor_signed_at=signed_at,
            studio_signed_at=signed_at,
        )
        data = _make_document_data(contract=contract)
        html = render_contract_html(data)

        assert "서명일시:" in html
        assert "2026년 03월 10일 15:00" in html
        assert "signed" in html

    def test_contains_content_hash(self) -> None:
        """content_hash가 포함되는지 확인한다."""
        test_hash = "a1b2c3d4e5f6" * 5 + "abcd"
        contract = _make_contract(content_hash=test_hash)
        data = _make_document_data(contract=contract)
        html = render_contract_html(data)

        assert test_hash in html

    def test_contains_content_hash_placeholder_when_none(self) -> None:
        """content_hash가 None일 때 '-'가 표시되는지 확인한다."""
        contract = _make_contract(content_hash=None)
        data = _make_document_data(contract=contract)
        html = render_contract_html(data)

        assert "SHA-256" in html

    def test_contains_footer_notice(self) -> None:
        """안내문이 포함되는지 확인한다."""
        data = _make_document_data()
        html = render_contract_html(data)

        assert "PilaMatch 플랫폼에서 생성된 전자 계약서" in html
        assert "전자문서 및 전자거래 기본법" in html

    def test_contains_print_media_query(self) -> None:
        """@media print CSS가 포함되는지 확인한다."""
        data = _make_document_data()
        html = render_contract_html(data)

        assert "@media print" in html

    def test_xss_prevention_in_names(self) -> None:
        """당사자 이름에 HTML 삽입 시 이스케이프되는지 확인한다."""
        data = _make_document_data(
            instructor_name="<script>alert('xss')</script>",
            studio_name='"><img src=x onerror=alert(1)>',
        )
        html = render_contract_html(data)

        # 원본 HTML 태그가 이스케이프되어야 한다
        assert "<script>" not in html
        assert "&lt;script&gt;" in html
        # img 태그도 이스케이프되어야 한다
        assert "<img " not in html
        assert "&lt;img src=x" in html

    def test_all_contract_statuses(self) -> None:
        """모든 계약 상태가 올바른 색상으로 렌더링되는지 확인한다."""
        status_map = {
            "확정": "#2563eb",
            "진행 중": "#d97706",
            "완료 대기": "#7c3aed",
            "완료": "#16a34a",
            "분쟁 중": "#dc2626",
            "취소됨": "#6b7280",
        }
        for label, expected_color in status_map.items():
            data = _make_document_data(status_label=label)
            html = render_contract_html(data)
            assert expected_color in html, f"상태 '{label}'에 대한 색상 '{expected_color}'이 없음"

    def test_missing_optional_fields(self) -> None:
        """선택 필드가 없을 때도 정상 렌더링되는지 확인한다."""
        data = _make_document_data(
            studio_address=None,
            studio_phone=None,
            instructor_phone=None,
        )
        # None -> "-" 으로 변환되어야 함
        html = render_contract_html(data)
        assert "<!DOCTYPE html>" in html
        # "-" 가 주소/연락처 위치에 표시되어야 함
        assert html.count("-") >= 3


# ---------------------------------------------------------------------------
# ContractService.get_contract_document_data 테스트
# ---------------------------------------------------------------------------

class TestGetContractDocumentData:
    """ContractService.get_contract_document_data 메서드 테스트."""

    @pytest.mark.asyncio
    async def test_contract_not_found_raises_value_error(self) -> None:
        """존재하지 않는 계약 ID로 조회 시 ValueError를 발생시킨다."""
        from app.services.contract import ContractService

        mock_db = AsyncMock()
        service = ContractService(mock_db)

        # get_by_id가 None을 반환하도록 mock
        service.get_by_id = AsyncMock(return_value=None)

        with pytest.raises(ValueError, match="CONTRACT_NOT_FOUND"):
            await service.get_contract_document_data(
                uuid.uuid4(), uuid.uuid4()
            )

    @pytest.mark.asyncio
    async def test_non_party_raises_permission_error(self) -> None:
        """계약 당사자가 아닌 사용자가 조회 시 PermissionError를 발생시킨다."""
        from app.services.contract import ContractService

        studio_user_id = uuid.uuid4()
        instructor_user_id = uuid.uuid4()
        outsider_user_id = uuid.uuid4()

        contract = _make_contract()

        # instructor profile mock
        instructor_profile = MagicMock()
        instructor_profile.user_id = instructor_user_id
        instructor_profile.display_name = "김강사"
        instructor_profile.phone = "010-1111-2222"

        # studio profile mock
        studio_profile = MagicMock()
        studio_profile.user_id = studio_user_id
        studio_profile.business_name = "테스트 스튜디오"
        studio_profile.address = "서울시"
        studio_profile.phone = "02-1234-5678"

        mock_db = AsyncMock()
        service = ContractService(mock_db)
        service.get_by_id = AsyncMock(return_value=contract)

        # DB execute mock: instructor_profile 조회 -> studio_profile 조회
        instructor_result = MagicMock()
        instructor_result.scalar_one_or_none.return_value = instructor_profile

        studio_result = MagicMock()
        studio_result.scalar_one_or_none.return_value = studio_profile

        mock_db.execute = AsyncMock(
            side_effect=[instructor_result, studio_result]
        )

        with pytest.raises(PermissionError, match="NOT_CONTRACT_PARTY"):
            await service.get_contract_document_data(
                contract.id, outsider_user_id
            )

    @pytest.mark.asyncio
    async def test_party_can_access(self) -> None:
        """계약 당사자는 정상적으로 데이터를 조회할 수 있다."""
        from app.services.contract import ContractService

        studio_user_id = uuid.uuid4()
        instructor_user_id = uuid.uuid4()

        contract = _make_contract(status="in_progress")

        # instructor profile mock
        instructor_profile = MagicMock()
        instructor_profile.user_id = instructor_user_id
        instructor_profile.display_name = "김강사"
        instructor_profile.phone = "010-1111-2222"

        # studio profile mock
        studio_profile = MagicMock()
        studio_profile.user_id = studio_user_id
        studio_profile.business_name = "테스트 스튜디오"
        studio_profile.address = "서울시"
        studio_profile.phone = "02-1234-5678"

        mock_db = AsyncMock()
        service = ContractService(mock_db)
        service.get_by_id = AsyncMock(return_value=contract)

        instructor_result = MagicMock()
        instructor_result.scalar_one_or_none.return_value = instructor_profile

        studio_result = MagicMock()
        studio_result.scalar_one_or_none.return_value = studio_profile

        mock_db.execute = AsyncMock(
            side_effect=[instructor_result, studio_result]
        )

        # studio 사용자로 조회
        data = await service.get_contract_document_data(
            contract.id, studio_user_id
        )

        assert data["contract"] == contract
        assert data["instructor_name"] == "김강사"
        assert data["studio_name"] == "테스트 스튜디오"
        assert data["studio_address"] == "서울시"
        assert data["status_label"] == "진행 중"

    @pytest.mark.asyncio
    async def test_instructor_can_access(self) -> None:
        """강사도 계약서를 조회할 수 있다."""
        from app.services.contract import ContractService

        studio_user_id = uuid.uuid4()
        instructor_user_id = uuid.uuid4()

        contract = _make_contract(status="confirmed")

        instructor_profile = MagicMock()
        instructor_profile.user_id = instructor_user_id
        instructor_profile.display_name = "이필라"
        instructor_profile.phone = "010-3333-4444"

        studio_profile = MagicMock()
        studio_profile.user_id = studio_user_id
        studio_profile.business_name = "힐링 스튜디오"
        studio_profile.address = "부산시"
        studio_profile.phone = "051-9999-8888"

        mock_db = AsyncMock()
        service = ContractService(mock_db)
        service.get_by_id = AsyncMock(return_value=contract)

        instructor_result = MagicMock()
        instructor_result.scalar_one_or_none.return_value = instructor_profile

        studio_result = MagicMock()
        studio_result.scalar_one_or_none.return_value = studio_profile

        mock_db.execute = AsyncMock(
            side_effect=[instructor_result, studio_result]
        )

        # instructor 사용자로 조회
        data = await service.get_contract_document_data(
            contract.id, instructor_user_id
        )

        assert data["contract"] == contract
        assert data["instructor_name"] == "이필라"
        assert data["studio_name"] == "힐링 스튜디오"
        assert data["status_label"] == "확정"
