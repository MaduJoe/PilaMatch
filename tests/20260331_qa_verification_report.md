# P0 E2E 테스트케이스 검증 종합 보고서

> **검증일:** 2026-03-01
> **검증 대상:** `tests/test_list.md` 15개 P0 TC
> **검증 방법:** 코드베이스 전수 정적 분석 (6개 병렬 에이전트)
> **판정:** BLOCKER 3건 미해결 → **릴리즈 불가**

---

## Executive Summary

| 지표 | 값 |
|------|----|
| 전체 TC | 15개 |
| PASS | 6개 |
| PARTIAL (수정 필요) | 5개 |
| FAIL (미구현/결함) | 4개 |
| Blocker급 결함 | **3건** |
| 기존 테스트 커버리지 | 4/15 완전, 5/15 부분, **6/15 미존재** |

---

## TC별 판정표

| TC | 테스트 항목 | 판정 | 심각도 | 핵심 이슈 |
|----|-----------|------|--------|----------|
| **TC-01** | 결제 성공 → HELD | ✅ PASS | - | `escrow_status` 기본값 의존 (명시적 설정 없음, 리스크 Low) |
| **TC-02** | 중복 결제 방지 | ✅ PASS | - | App-level + Toss Idempotency-Key 이중 보호. 완벽 |
| **TC-03** | 결제 실패/취소 상태 오염 방지 | ✅ PASS | - | FAILED/CANCELLED 상태 정상 전환 |
| **TC-04** | 완료 → RELEASED → Free 5% | ❌ FAIL | **BLOCKER** | 에스크로에서 이중 수수료 차감 + 하드코딩 5% |
| **TC-05** | Premium 3% 정산 | ❌ FAIL | **BLOCKER** | `escrow.py`가 멤버십 무시, 항상 5% 적용 |
| **TC-06** | 상태머신 불법 전이 차단 | ⚠️ PARTIAL | HIGH | `cancel()`만 `_validate_transition()` 사용. 나머지 우회 가능 |
| **TC-07** | 취소 → REFUNDED | ✅ PASS | - | 전액/부분 환불 + 멱등성 정상 |
| **TC-08** | 보증금 잔존 기능 제거 | ✅ PASS | LOW | 코드 deprecated 완료. 법적 문서/README에 잔존 문구 |
| **TC-09** | 프로필 69% 차단 | ✅ PASS | - | 서버사이드 강제. 우회 불가 |
| **TC-10** | 프로필 70% 진입 허용 | ✅ PASS | - | 정상 동작 |
| **TC-11** | Free 동시 지원 5개 제한 | ⚠️ PARTIAL | MEDIUM | "동시" 아닌 "일일"로 구현. 에러코드 불일치 |
| **TC-12** | Premium 무제한 지원 | ✅ PASS | - | `membership_tier=premium` 시 무제한 |
| **TC-13** | 긴급매칭 Premium 전용 | ❌ FAIL | **BLOCKER** | 목록 필터링만 존재. 상세보기/지원 API 무방비 |
| **TC-14** | Premium 부스트 1.3x | ✅ PASS | - | `min(100, round(total * 1.3))` 정확 |
| **TC-15** | 템플릿 CRUD + 상한 10개 | ⚠️ PARTIAL | HIGH | DB 제약조건 없음. 동시 요청 시 11개+ 생성 가능 |

---

## BLOCKER급 결함 상세 (출시 전 반드시 수정)

### BLOCKER #1: 에스크로 수수료 이중 차감 + 멤버십 무시

**영향 TC:** TC-04, TC-05
**파일:** `backend/app/services/escrow.py:23, 55-58`

```
문제 흐름:
  contract.total_amount = 100,000원
  payment.amount = 105,000원 (초기화 시 5% 수수료 포함)

  에스크로 RELEASE 시:
    total = payment.amount = 105,000  ← payment에 이미 수수료 포함!
    platform_fee = 105,000 × 5% = 5,250  ← 이중 차감!
    instructor_payout = 99,750원  ← 실제: 95,000이어야 함
```

**결함 2가지:**
1. `PLATFORM_FEE_PERCENT = 0.05` 하드코딩 → Premium 3% 무시
2. `payment.amount`(수수료 포함 금액) 기준 재차감 → 금액 오류

**수정 방향:**
- `release_escrow_to_instructor()`에 멤버십 기반 수수료율 전달
- `contract.total_amount` 기준으로 수수료 계산하도록 변경

---

### BLOCKER #2: 긴급매칭 접근 제어 미구현

**영향 TC:** TC-13
**파일:** `backend/app/api/v1/endpoints/job_posts.py:246-261`, `backend/app/services/application.py:29-77`

```
현재 상태:
  ✅ 매칭 리스트 (/for-me): Free 필터링 됨
  ❌ 상세 보기 (GET /{id}): 누구나 접근 가능
  ❌ 지원 (POST /applications): is_urgent 체크 없음

→ Free 사용자가 job_post_id를 알면 직접 API로 긴급공고 지원 가능
→ PREMIUM_REQUIRED 에러코드 미구현
```

**수정 방향:**
- `GET /job-posts/{id}` 에 is_urgent 체크 + Premium 검증 추가
- `ApplicationService.create()` 에 긴급공고 지원 시 Premium 검증 추가
- `PREMIUM_REQUIRED` 에러코드 반환

---

### BLOCKER #3: 상태머신 일관성 부재

**영향 TC:** TC-06
**파일:** `backend/app/services/contract.py`, `backend/app/services/dispute.py`

| 엔드포인트 | `_validate_transition()` 사용 | 에러코드 |
|-----------|---------------------------|---------|
| `cancel()` | ✅ 사용 | `INVALID_STATE_TRANSITION` |
| `set_in_progress()` | ❌ 커스텀 체크 | `UPDATE_FAILED` (불일치) |
| `confirm_completion()` | ❌ 커스텀 allowlist | `CONFIRM_FAILED` (불일치) |
| `dispute.resolve()` | ❌ 직접 상태 할당 | 검증 없음 |

**수정 방향:**
- 모든 상태 전이 메서드에서 `_validate_transition()` 통일 호출
- 에러코드를 `INVALID_STATE_TRANSITION`으로 통일
- `dispute.py`에서도 계약 상태 변경 시 validation 추가

---

## HIGH 리스크 결함

### HIGH #1: 템플릿 상한 레이스 컨디션 (TC-15)

**파일:** `backend/app/services/application_template.py:35-42`

- `SELECT COUNT` → `INSERT` 사이에 동시 요청 가능
- DB에 `UNIQUE CONSTRAINT` 또는 `CHECK` 없음
- `SELECT ... FOR UPDATE` 미사용
- **결과:** 동시 2요청 시 11개 생성 가능

**수정 방향:**
- `SELECT COUNT(*) ... FOR UPDATE` 사용하여 비관적 잠금 적용
- 또는 DB 레벨 트리거/CHECK 제약조건 추가

### HIGH #2: 지원 제한 정의 불일치 (TC-11)

**파일:** `backend/app/services/daily_usage.py:61-86`

| 항목 | TC 스펙 | 실제 구현 |
|------|---------|----------|
| 제한 유형 | "동시 지원 5개" | "일일 5회" (자정 리셋) |
| 에러코드 | `APPLICATION_LIMIT` | `APPLICATION_FAILED` |
| 철회 후 재지원 | 가능해야 함 | 불가 (카운터 유지) |

**수정 방향 (2가지 중 택 1):**
- **옵션 A:** "동시 활성 지원" 기준으로 변경 → `get_active_application_count()` 활용
- **옵션 B:** TC-11 스펙을 "일일 5회"로 수정 (정책 결정 필요)
- `APPLICATION_LIMIT` 에러코드 핸들러를 `applications.py:62`에 추가

---

## 보증금 잔존 문구 (TC-08, LOW)

코드상 deprecated 완료되었으나, 아래 문서에 잔존 문구 있음:

| 파일 | 잔존 내용 | 영향 |
|------|----------|------|
| `frontend-next/src/lib/constants.ts:80` | "30,000원 패널티가 보증금에서 차감" | 계약 약관에 노출 |
| `frontend-next/src/app/(legal)/terms/page.tsx:24-89` | 보증금 50,000원 언급 | 이용약관 페이지 |
| `frontend-next/src/app/(legal)/refund/page.tsx:82-93` | 노쇼 패널티 보증금 차감 | 환불정책 페이지 |
| `frontend-next/src/app/(legal)/privacy/page.tsx:37` | 보증금 관리 언급 | 개인정보처리방침 |
| `README.md:40, 366-367, 838-843` | 보증금 API/플로우 설명 | 개발 문서 |
| `backend/app/services/escrow.py:8-9` | 보증금 차감 관련 주석 | 코드 주석 |

---

## 테스트 커버리지 현황

### 기존 테스트: 280개 / 25개 파일

| TC | 테스트 존재 | 커버리지 수준 | 파일 |
|----|-----------|-------------|------|
| TC-01 | ⚠️ 부분 | 초기화만, HELD 상태 미검증 | `test_payment_webhook.py` |
| TC-02 | ✅ 있음 | 멱등성 검증 완료 | `test_payment_webhook.py::test_payment_idempotency` |
| TC-03 | ⚠️ 부분 | 취소만, 실패 시나리오 없음 | `test_payment_cancel.py` |
| TC-04 | ⚠️ 부분 | 에스크로 Mock 처리됨 | `test_contract_state_machine.py` |
| TC-05 | ✅ 있음 | 단위 수준 (Mock) | `test_contract_state_machine.py::test_completion_fee_rate_premium` |
| TC-06 | ✅ 있음 | 단위 테스트 수준 | `test_contract_state_machine.py` |
| TC-07 | ✅ 있음 | 9개 테스트 | `test_payment_cancel.py` |
| TC-08 | ❌ 없음 | - | - |
| TC-09 | ❌ 없음 | - | - |
| TC-10 | ❌ 없음 | - | - |
| TC-11 | ❌ 없음 | - | - |
| TC-12 | ❌ 없음 | - | - |
| TC-13 | ❌ 없음 | - | - |
| TC-14 | ❌ 없음 | - | - |
| TC-15 | ❌ 없음 | - | - |

---

## 권고 액션 (우선순위)

### P0 - 출시 차단 (즉시 수정)

| # | 액션 | 파일 | 예상 난이도 |
|---|------|------|-----------|
| 1 | `escrow.py` 수수료를 멤버십 기반으로 변경 + `contract.total_amount` 사용 | `escrow.py` | Medium |
| 2 | 긴급공고 상세보기 + 지원 API에 Premium 체크 추가 | `job_posts.py`, `application.py` | Low |
| 3 | 모든 상태 전이 엔드포인트에 `_validate_transition()` 통일 | `contract.py` | Medium |

### P1 - 출시 전 강력 권고

| # | 액션 | 파일 |
|---|------|------|
| 4 | 지원 제한을 "동시 활성" 기준으로 변경하거나 TC-11 스펙 수정 | `daily_usage.py` |
| 5 | `APPLICATION_LIMIT` 에러코드 핸들러 추가 | `applications.py:62` |
| 6 | 템플릿 상한에 DB 제약조건 또는 `SELECT FOR UPDATE` 추가 | `application_template.py`, migration |
| 7 | 법적 문서(약관/환불정책)에서 보증금 문구 삭제 | `constants.ts`, legal pages |

### P2 - TC 테스트 추가 (6개 미존재)

| TC | 테스트 추가 대상 |
|----|---------------|
| TC-08 | 보증금 미작동 통합 테스트 |
| TC-09/10 | 프로필 완성도 게이트 (경계값 69%/70%) |
| TC-11/12 | 지원 제한 (Free 5개 / Premium 무제한) |
| TC-13 | 긴급매칭 접근제어 |
| TC-14 | 부스트 점수 계산 |
| TC-15 | 템플릿 CRUD + 동시성 |

---

## 코드 참조 (전체)

| 항목 | 파일 | 라인 |
|------|------|------|
| Escrow 상태 필드 | `backend/app/models/payment.py` | 28 |
| Payment 초기화 (하드코딩 수수료) | `backend/app/services/payment.py` | 26, 107-110 |
| Payment 확인 | `backend/app/services/payment.py` | 134-172 |
| Escrow 릴리즈 (버그) | `backend/app/services/escrow.py` | 23, 55-58 |
| 계약 완료 (정상 수수료) | `backend/app/services/contract.py` | 373-384 |
| 수수료율 조회 | `backend/app/services/contract.py` | 72-95 |
| 상태 전이 검증 | `backend/app/services/contract.py` | 18-26 |
| Payment 취소 | `backend/app/services/payment.py` | 213-310 |
| 프로필 완성도 | `backend/app/services/profile_completeness.py` | 82-154 |
| 지원 생성 (게이트) | `backend/app/services/application.py` | 54-77 |
| 일일 사용량 제한 | `backend/app/services/daily_usage.py` | 39-86 |
| 긴급 매칭 필터 | `backend/app/api/v1/endpoints/job_posts.py` | 174-185 |
| 긴급 매칭 상세 (미검증) | `backend/app/api/v1/endpoints/job_posts.py` | 246-261 |
| Premium 부스트 | `backend/app/services/matching.py` | 101-106 |
| 템플릿 서비스 | `backend/app/services/application_template.py` | 28-42 |
| 템플릿 API | `backend/app/api/v1/endpoints/templates.py` | 68-109 |
| 분쟁 상태 변경 (우회) | `backend/app/services/dispute.py` | 103, 221-227 |
| 보증금 서비스 (deprecated) | `backend/app/services/deposit.py` | 전체 |

---

## 최종 릴리즈 게이트 판정

```
┌─────────────────────────────────────────────┐
│  BLOCKER 3건 미해결 → ❌ 릴리즈 불가        │
│                                             │
│  #1 에스크로 수수료 이중차감 + 멤버십 무시   │
│  #2 긴급매칭 접근제어 미구현                 │
│  #3 상태머신 _validate_transition() 미통일   │
│                                             │
│  BLOCKER 수정 후 재검증 시 릴리즈 가능       │
└─────────────────────────────────────────────┘
```

---

*Generated by QA Verification Engine | 2026-03-01*
