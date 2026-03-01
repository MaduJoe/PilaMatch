"""계약서 HTML 문서 렌더링 서비스.

브라우저에서 Ctrl+P로 PDF 인쇄가 가능한 HTML 계약서를 생성한다.
외부 PDF 라이브러리 의존성 없이 순수 HTML + CSS @media print로 구현.
"""

from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

# 계약 상태별 배지 색상
_STATUS_COLORS: Dict[str, str] = {
    "확정": "#2563eb",
    "진행 중": "#d97706",
    "완료 대기": "#7c3aed",
    "완료": "#16a34a",
    "분쟁 중": "#dc2626",
    "취소됨": "#6b7280",
}


def _fmt_datetime(dt: Optional[object]) -> str:
    """datetime 객체를 한국어 형식 문자열로 변환한다.

    Args:
        dt: datetime 객체 또는 None.

    Returns:
        포맷된 문자열. None이면 "-".
    """
    if dt is None:
        return "-"
    return dt.strftime("%Y년 %m월 %d일 %H:%M")


def _fmt_date(d: Optional[object]) -> str:
    """date 객체를 한국어 형식 문자열로 변환한다.

    Args:
        d: date 객체 또는 None.

    Returns:
        포맷된 문자열. None이면 "-".
    """
    if d is None:
        return "-"
    return d.strftime("%Y년 %m월 %d일")


def _fmt_time(t: Optional[object]) -> str:
    """time 객체를 HH:MM 형식 문자열로 변환한다.

    Args:
        t: time 객체 또는 None.

    Returns:
        포맷된 문자열. None이면 "-".
    """
    if t is None:
        return "-"
    return t.strftime("%H:%M")


def _fmt_amount(amount: Optional[object]) -> str:
    """금액을 한국 원화 형식 문자열로 변환한다.

    Args:
        amount: Decimal/float 금액 또는 None.

    Returns:
        포맷된 금액 문자열. None이면 "-".
    """
    if amount is None:
        return "-"
    return f"{int(amount):,}원"


def _escape_html(text: Optional[str]) -> str:
    """HTML 특수문자를 이스케이프한다.

    Args:
        text: 원본 문자열.

    Returns:
        이스케이프된 문자열. None이면 빈 문자열.
    """
    if text is None:
        return ""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#x27;")
    )


def render_contract_html(data: Dict) -> str:
    """계약서 데이터를 HTML 문서로 렌더링한다.

    Args:
        data: ContractService.get_contract_document_data()가 반환한 딕셔너리.

    Returns:
        완성된 HTML 문서 문자열.
    """
    contract = data["contract"]
    studio_name = _escape_html(data["studio_name"])
    instructor_name = _escape_html(data["instructor_name"])
    studio_address = _escape_html(data.get("studio_address") or "-")
    studio_phone = _escape_html(data.get("studio_phone") or "-")
    instructor_phone = _escape_html(data.get("instructor_phone") or "-")
    status_label = _escape_html(data["status_label"])
    status_color = _STATUS_COLORS.get(data["status_label"], "#6b7280")

    contract_id = str(contract.id)
    content_hash = _escape_html(contract.content_hash) if contract.content_hash else "-"

    logger.info("계약서 HTML 렌더링: contract_id=%s", contract_id)

    return f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>PilaMatch 전자 계약서 - {contract_id[:8]}</title>
<style>
  /* ===== 기본 스타일 ===== */
  * {{
    margin: 0;
    padding: 0;
    box-sizing: border-box;
  }}
  body {{
    font-family: 'Pretendard', -apple-system, BlinkMacSystemFont, 'Segoe UI',
                 'Noto Sans KR', sans-serif;
    color: #1f2937;
    background: #f3f4f6;
    line-height: 1.6;
  }}
  .container {{
    max-width: 800px;
    margin: 40px auto;
    background: #ffffff;
    border-radius: 8px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    overflow: hidden;
  }}

  /* ===== 헤더 ===== */
  .header {{
    background: linear-gradient(135deg, #1e3a5f 0%, #2563eb 100%);
    color: #ffffff;
    padding: 32px 40px;
    text-align: center;
  }}
  .header h1 {{
    font-size: 24px;
    font-weight: 700;
    margin-bottom: 4px;
  }}
  .header .subtitle {{
    font-size: 14px;
    opacity: 0.85;
  }}

  /* ===== 본문 ===== */
  .body {{
    padding: 40px;
  }}

  /* 계약 번호 & 상태 */
  .meta-row {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 32px;
    padding-bottom: 16px;
    border-bottom: 2px solid #e5e7eb;
  }}
  .contract-id {{
    font-size: 13px;
    color: #6b7280;
  }}
  .contract-id strong {{
    color: #1f2937;
  }}
  .status-badge {{
    display: inline-block;
    padding: 4px 14px;
    border-radius: 9999px;
    font-size: 13px;
    font-weight: 600;
    color: #ffffff;
    background: {status_color};
  }}

  /* 섹션 */
  .section {{
    margin-bottom: 28px;
  }}
  .section-title {{
    font-size: 16px;
    font-weight: 700;
    color: #1e3a5f;
    margin-bottom: 12px;
    padding-left: 12px;
    border-left: 4px solid #2563eb;
  }}

  /* 테이블 */
  table {{
    width: 100%;
    border-collapse: collapse;
  }}
  table th,
  table td {{
    padding: 10px 14px;
    font-size: 14px;
    text-align: left;
    border-bottom: 1px solid #e5e7eb;
  }}
  table th {{
    width: 140px;
    background: #f9fafb;
    color: #374151;
    font-weight: 600;
  }}
  table td {{
    color: #1f2937;
  }}

  /* 서명 영역 */
  .signatures {{
    display: flex;
    gap: 24px;
    margin-top: 8px;
  }}
  .sig-box {{
    flex: 1;
    border: 1px solid #d1d5db;
    border-radius: 6px;
    padding: 16px;
    text-align: center;
  }}
  .sig-box .role {{
    font-size: 13px;
    font-weight: 600;
    color: #6b7280;
    margin-bottom: 4px;
  }}
  .sig-box .name {{
    font-size: 16px;
    font-weight: 700;
    color: #1f2937;
    margin-bottom: 8px;
  }}
  .sig-box .sig-date {{
    font-size: 12px;
    color: #9ca3af;
  }}
  .sig-box.signed {{
    border-color: #16a34a;
    background: #f0fdf4;
  }}
  .sig-box.signed .sig-date {{
    color: #16a34a;
  }}

  /* 위변조 방지 */
  .hash-section {{
    margin-top: 32px;
    padding: 16px;
    background: #f9fafb;
    border: 1px dashed #d1d5db;
    border-radius: 6px;
    font-size: 12px;
    color: #6b7280;
    word-break: break-all;
  }}
  .hash-section strong {{
    color: #374151;
  }}

  /* 푸터 */
  .footer {{
    padding: 24px 40px;
    background: #f9fafb;
    border-top: 1px solid #e5e7eb;
    text-align: center;
    font-size: 12px;
    color: #9ca3af;
  }}
  .footer .notice {{
    margin-bottom: 4px;
  }}

  /* ===== 인쇄 스타일 ===== */
  @media print {{
    body {{
      background: #ffffff;
    }}
    .container {{
      margin: 0;
      box-shadow: none;
      border-radius: 0;
    }}
    .header {{
      -webkit-print-color-adjust: exact;
      print-color-adjust: exact;
    }}
    .status-badge {{
      -webkit-print-color-adjust: exact;
      print-color-adjust: exact;
    }}
    .sig-box.signed {{
      -webkit-print-color-adjust: exact;
      print-color-adjust: exact;
    }}
    .no-print {{
      display: none !important;
    }}
  }}

  /* ===== 반응형 ===== */
  @media (max-width: 640px) {{
    .body {{
      padding: 24px 20px;
    }}
    .header {{
      padding: 24px 20px;
    }}
    .signatures {{
      flex-direction: column;
    }}
    table th {{
      width: 100px;
    }}
  }}
</style>
</head>
<body>
<div class="container">

  <!-- 헤더 -->
  <div class="header">
    <h1>PilaMatch 전자 계약서</h1>
    <div class="subtitle">필라테스/요가 강사-스튜디오 수업 계약</div>
  </div>

  <div class="body">
    <!-- 계약 번호 & 상태 -->
    <div class="meta-row">
      <div class="contract-id">
        계약번호: <strong>{_escape_html(contract_id)}</strong>
      </div>
      <span class="status-badge">{status_label}</span>
    </div>

    <!-- 1. 당사자 정보 -->
    <div class="section">
      <div class="section-title">당사자 정보</div>
      <table>
        <tr>
          <th>스튜디오</th>
          <td>{studio_name}</td>
        </tr>
        <tr>
          <th>스튜디오 주소</th>
          <td>{studio_address}</td>
        </tr>
        <tr>
          <th>스튜디오 연락처</th>
          <td>{studio_phone}</td>
        </tr>
        <tr>
          <th>강사</th>
          <td>{instructor_name}</td>
        </tr>
        <tr>
          <th>강사 연락처</th>
          <td>{instructor_phone}</td>
        </tr>
      </table>
    </div>

    <!-- 2. 수업 정보 -->
    <div class="section">
      <div class="section-title">수업 정보</div>
      <table>
        <tr>
          <th>수업 날짜</th>
          <td>{_fmt_date(contract.date)}</td>
        </tr>
        <tr>
          <th>수업 시간</th>
          <td>{_fmt_time(contract.start_time)} ~ {_fmt_time(contract.end_time)}</td>
        </tr>
        <tr>
          <th>총 회차</th>
          <td>{contract.total_sessions}회</td>
        </tr>
      </table>
    </div>

    <!-- 3. 금액 정보 -->
    <div class="section">
      <div class="section-title">금액 정보</div>
      <table>
        <tr>
          <th>시급</th>
          <td>{_fmt_amount(contract.hourly_rate)}</td>
        </tr>
        <tr>
          <th>총 계약 금액</th>
          <td><strong>{_fmt_amount(contract.total_amount)}</strong></td>
        </tr>
        <tr>
          <th>플랫폼 수수료</th>
          <td>{_fmt_amount(contract.platform_fee)}</td>
        </tr>
        <tr>
          <th>정산 금액</th>
          <td>{_fmt_amount(contract.settlement_amount)}</td>
        </tr>
      </table>
    </div>

    <!-- 4. 서명 정보 -->
    <div class="section">
      <div class="section-title">전자 서명</div>
      <div class="signatures">
        <div class="sig-box {"signed" if contract.studio_signed_at else ""}">
          <div class="role">스튜디오 (갑)</div>
          <div class="name">{studio_name}</div>
          <div class="sig-date">
            {"서명일시: " + _fmt_datetime(contract.studio_signed_at) if contract.studio_signed_at else "미서명"}
          </div>
        </div>
        <div class="sig-box {"signed" if contract.instructor_signed_at else ""}">
          <div class="role">강사 (을)</div>
          <div class="name">{instructor_name}</div>
          <div class="sig-date">
            {"서명일시: " + _fmt_datetime(contract.instructor_signed_at) if contract.instructor_signed_at else "미서명"}
          </div>
        </div>
      </div>
    </div>

    <!-- 5. 계약 일시 -->
    <div class="section">
      <div class="section-title">계약 이력</div>
      <table>
        <tr>
          <th>계약 생성일</th>
          <td>{_fmt_datetime(contract.created_at)}</td>
        </tr>
        <tr>
          <th>최종 수정일</th>
          <td>{_fmt_datetime(contract.updated_at)}</td>
        </tr>
        <tr>
          <th>계약 상태</th>
          <td>{status_label}</td>
        </tr>
      </table>
    </div>

    <!-- 6. 위변조 방지 해시 -->
    <div class="hash-section">
      <strong>콘텐츠 무결성 해시 (SHA-256):</strong><br>
      {content_hash}
      <br><br>
      <strong>검증 방법:</strong> 양측 서명 완료 시 계약 핵심 내용(금액, 일시, 당사자)의
      SHA-256 해시가 생성됩니다. 이 해시값이 위 값과 일치하면 계약 내용이
      서명 이후 변경되지 않았음을 확인할 수 있습니다.
    </div>
  </div>

  <!-- 푸터 -->
  <div class="footer">
    <div class="notice">
      이 문서는 PilaMatch 플랫폼에서 생성된 전자 계약서입니다.
    </div>
    <div class="notice">
      본 계약서는 전자문서 및 전자거래 기본법에 따라 법적 효력을 갖습니다.
    </div>
    <div>
      문의: support@pilamatch.com | https://pilamatch.com
    </div>
  </div>

</div>
</body>
</html>"""
