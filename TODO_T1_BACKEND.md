# T1: Backend API + Services — TODO

## 이 터미널의 역할

Backend API 라우터, 서비스 로직, 결제/인증 관련 작업 담당.

**담당 파일 범위:**
- `backend/app/api/v1/endpoints/` — REST 라우터
- `backend/app/services/` — 비즈니스 로직
- `backend/app/schemas/` — Pydantic 스키마
- `backend/app/core/` — Config, Security, Deps

**CLAUDE.md 에이전트:** `backend-api`, `payment-trust`

---

## TODO 목록

| # | 우선순위 | 작업 | 의존성 |
|---|---------|------|--------|
| 1 | CRITICAL | Payout 모델 + PayoutStatus enum 생성 | - |
| 2 | CRITICAL | Payment 모델 누락 필드 추가 | - |
| 3 | HIGH | TossPayments webhook 서명 검증 | - |
| 4 | HIGH | 에스크로 환불 API 실제 구현 | - |
| 5 | HIGH | CORS 도메인 제한 설정 | - |
| 6 | HIGH | JWT refresh token + 블랙리스트 | T4-#22 (Redis) 먼저 |
| 7 | MEDIUM | Rate limiting (slowapi) | - |
| 8 | MEDIUM | N+1 쿼리 제거 + 페이지네이션 | - |

---

## 작업 상세

### #1 — Payout 모델 + PayoutStatus enum 생성 [CRITICAL]

**문제:** `payment.py:13`에서 `Payout` 모델을 import하고 `payment.py:240-248`에서 사용하지만, 모델 파일이 존재하지 않음. `enums.py`에도 `PayoutStatus`가 없음.

**수정 파일:**
- `backend/app/models/payout.py` — 새 파일 생성
- `backend/app/models/enums.py:33-48` — PayoutStatus enum 추가
- `backend/app/models/__init__.py` — Payout export 추가

**수정 내용:**
```python
# enums.py에 추가
class PayoutStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

# payout.py 모델 생성
class Payout(Base, TimestampMixin):
    __tablename__ = "payouts"
    id = Column(GUID(), primary_key=True, default=uuid4)
    contract_id = Column(GUID(), ForeignKey("contracts.id"), nullable=False)
    instructor_id = Column(GUID(), ForeignKey("users.id"), nullable=False)
    amount = Column(Integer, nullable=False)          # 정산 금액
    platform_fee = Column(Integer, default=0)         # 플랫폼 수수료
    status = Column(String(20), default="pending")
    paid_at = Column(DateTime, nullable=True)
    bank_code = Column(String(10), nullable=True)
    account_number = Column(String(50), nullable=True)
```

**프롬프트 예시:**
```
backend/app/models/enums.py에 PayoutStatus enum을 추가하고,
backend/app/models/payout.py 파일을 새로 생성해서 Payout 모델을 만들어줘.
payment.py:13, payment.py:240-248에서 import해서 쓰고 있어.
models/__init__.py에도 export 추가해줘.
```

---

### #2 — Payment 모델 누락 필드 추가 [CRITICAL]

**문제:** `payment.py` 서비스에서 여러 필드를 사용하지만 `models/payment.py`에 정의되지 않음.

**수정 파일:**
- `backend/app/models/payment.py:1-30` — 필드 추가
- `backend/app/schemas/payment.py:15-24` — 응답 스키마에 필드 추가

**누락 필드 목록:**
| 필드 | 사용 위치 | 타입 |
|------|----------|------|
| `order_id` | payment.py:38, 74, 91, 106 | `String(100)` |
| `payer_user_id` | payment.py:87-88 | `GUID(), ForeignKey("users.id")` |
| `payment_method` | payment.py:125 | `String(30)` |
| `failure_reason` | payment.py:116, 129, 189 | `Text` |
| `pg_response` | payment.py:126, 191 | `JSON` |
| `cancelled_at` | - | `DateTime` |

또한 `enums.py`의 PaymentStatus에 `REFUNDED` 값 추가 필요 (payment.py:186에서 사용).

**프롬프트 예시:**
```
backend/app/models/payment.py에 order_id, payer_user_id, payment_method,
failure_reason, pg_response, cancelled_at 필드를 추가해줘.
enums.py의 PaymentStatus에 REFUNDED도 추가해줘.
schemas/payment.py의 PaymentResponse에도 반영해줘.
```

---

### #3 — TossPayments webhook 서명 검증 [HIGH]

**문제:** `payment.py:171-192`의 `handle_webhook()`에서 Toss 서명 검증 없이 payload를 처리함.

**수정 파일:**
- `backend/app/services/payment.py:171-192` — HMAC-SHA256 서명 검증 추가
- `backend/app/core/config.py` — `TOSS_WEBHOOK_SECRET` 설정 추가

**수정 내용:**
```python
import hmac, hashlib

def _verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
    expected = hmac.new(
        settings.TOSS_WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
```

**프롬프트 예시:**
```
payment.py의 handle_webhook()에 Toss webhook 서명 검증 로직을 추가해줘.
HMAC-SHA256으로 검증하고, 실패하면 403 반환.
config.py에 TOSS_WEBHOOK_SECRET 환경변수도 추가해줘.
```

---

### #4 — 에스크로 환불 API 실제 구현 [HIGH]

**문제:** 에스크로 환불이 실제 Toss API를 호출하지 않고 DB 상태만 변경함.

**수정 파일:**
- `backend/app/services/payment.py` — Toss 환불 API 호출 구현
- `backend/app/api/v1/endpoints/payments.py` — 환불 엔드포인트 확인

**수정 내용:**
- Toss `POST /v1/payments/{paymentKey}/cancel` API 호출
- 환불 사유, 환불 금액 파라미터 처리
- 부분 환불 지원

**프롬프트 예시:**
```
payment.py에서 에스크로 환불 시 실제 Toss Payments API를 호출하도록 구현해줘.
현재는 DB 상태만 바꾸고 있어. POST /v1/payments/{paymentKey}/cancel 호출 필요.
부분 환불도 지원해야 함.
```

---

### #5 — CORS 도메인 제한 설정 [HIGH]

**문제:** `backend/app/main.py:18`에서 `allow_origins=["*"]`로 설정됨. `allow_credentials=True`와 함께 사용하면 CORS 스펙 위반.

**수정 파일:**
- `backend/app/main.py:15-22` — CORS 설정 수정
- `backend/app/core/config.py` — `ALLOWED_ORIGINS` 환경변수 추가

**수정 내용:**
```python
# config.py
ALLOWED_ORIGINS: list[str] = ["http://localhost:8501", "https://pilamatch.com"]

# main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,  # NOT ["*"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**프롬프트 예시:**
```
main.py:18의 CORS allow_origins=["*"]를 환경변수 기반으로 수정해줘.
config.py에 ALLOWED_ORIGINS 설정 추가하고, 개발환경은 localhost:8501, 프로덕션은 실제 도메인만 허용.
```

---

### #6 — JWT refresh token + 블랙리스트 [HIGH]

**의존성:** T4-#22 (Redis 서비스 추가) 완료 후 작업

**문제:** `core/security.py:19-27`에 `create_access_token()`만 존재. refresh token 없음. 토큰 만료 시간이 7일(10080분)으로 너무 김.

**수정 파일:**
- `backend/app/core/security.py:19-27` — refresh token 생성 함수 추가
- `backend/app/api/v1/endpoints/auth.py` — `/refresh` 엔드포인트 추가
- `backend/app/core/deps.py:16-44` — 토큰 블랙리스트 확인 로직 추가

**수정 내용:**
- access token 만료: 15분
- refresh token 만료: 7일
- Redis에 블랙리스트 저장 (로그아웃 시)

**프롬프트 예시:**
```
JWT에 refresh token 메커니즘을 추가해줘.
security.py에 create_refresh_token() 추가, access token은 15분으로 줄이고,
auth.py에 POST /refresh 엔드포인트 추가.
Redis를 사용한 토큰 블랙리스트도 구현해줘.
```

---

### #7 — Rate limiting (slowapi) [MEDIUM]

**문제:** API에 rate limiting이 없어서 DoS 공격에 취약.

**수정 파일:**
- `backend/app/main.py` — slowapi 미들웨어 추가
- `backend/app/api/v1/endpoints/auth.py` — 로그인 엔드포인트에 rate limit 적용

**수정 내용:**
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@router.post("/login")
@limiter.limit("5/minute")
async def login(request: Request, ...):
```

**프롬프트 예시:**
```
slowapi를 사용해서 rate limiting을 추가해줘.
전역 기본: 100/분, 로그인: 5/분, 결제: 10/분.
main.py에 미들웨어 등록하고 주요 엔드포인트에 적용해줘.
```

---

### #8 — N+1 쿼리 제거 + 페이지네이션 [MEDIUM]

**문제:** 리스트 조회 API에 eager loading과 페이지네이션이 없음.

**수정 파일:**
- `backend/app/services/application.py` — selectinload 추가
- `backend/app/services/contract.py` — selectinload 추가
- `backend/app/api/v1/endpoints/applications.py` — 페이지네이션 파라미터
- `backend/app/api/v1/endpoints/contracts.py` — 페이지네이션 파라미터

**수정 내용:**
```python
from sqlalchemy.orm import selectinload

query = select(Application).options(
    selectinload(Application.instructor),
    selectinload(Application.job_post)
).offset(skip).limit(limit)
```

**프롬프트 예시:**
```
application, contract 리스트 조회에 selectinload로 N+1 쿼리를 제거하고,
skip/limit 기반 페이지네이션을 추가해줘. 기본 limit=20, 최대 100.
```

---

## 실행 순서 가이드

```
1라운드: #1 (Payout 모델) + #2 (Payment 필드) — 병렬 가능
   ↓
2라운드: #3 (webhook 검증) + #4 (환불 구현) + #5 (CORS) — 병렬 가능
   ↓
3라운드: #6 (JWT refresh, Redis 필요) + #7 (Rate limiting) + #8 (N+1/페이지네이션)
```

## 완료 체크리스트

- [x] #1 Payout 모델이 import 에러 없이 동작
- [x] #2 Payment 서비스가 모든 필드를 정상 저장
- [x] #3 webhook에 잘못된 서명 보내면 403 반환
- [x] #4 Toss 환불 API 호출 후 DB 상태 업데이트
- [x] #5 CORS가 환경변수 기반으로 동작
- [ ] #6 access/refresh token 정상 발급 및 갱신
- [x] #7 rate limit 초과 시 429 반환
- [x] #8 리스트 API에 페이지네이션 동작
