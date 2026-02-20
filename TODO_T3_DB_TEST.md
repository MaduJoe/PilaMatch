# T3: Database + Tests + Security — TODO

## 이 터미널의 역할

DB 스키마 변경, Alembic 마이그레이션, 테스트 작성/실행, 보안 리뷰 담당.

**담당 파일 범위:**
- `backend/app/models/` — SQLAlchemy 모델
- `backend/alembic/` — 마이그레이션
- `tests/` — pytest 테스트
- `backend/app/core/security.py` — 보안 로직

**CLAUDE.md 에이전트:** `database`, `test-qa`, `security-reviewer`

---

## TODO 목록

| # | 우선순위 | 작업 | 의존성 |
|---|---------|------|--------|
| 15 | CRITICAL | Payout 마이그레이션 + Payment 필드 마이그레이션 | T1-#1, T1-#2 먼저 |
| 16 | HIGH | OTP 저장소 Redis 이전 | T4-#22 먼저 |
| 17 | MEDIUM | DB 커넥션 풀 설정 | - |
| 18 | MEDIUM | 결제 플로우 E2E 테스트 | T1-#1,#2,#3 먼저 |
| 19 | MEDIUM | 계약 상태 전이 + 검증 테스트 | - |
| 20 | LOW | 보안 리뷰 실행 | T1-#5,#6,#7 먼저 |

---

## 작업 상세

### #15 — Payout 마이그레이션 + Payment 필드 마이그레이션 [CRITICAL]

**의존성:** T1-#1 (Payout 모델) + T1-#2 (Payment 필드) 머지 후 작업

**문제:** T1에서 Payout 모델 생성 및 Payment 필드 추가 후, Alembic 마이그레이션이 필요.

**수정 파일:**
- `backend/alembic/versions/` — 새 마이그레이션 파일 자동 생성

**실행 순서:**
```bash
# 1. T1 브랜치를 main에 머지한 후, T3에서 main을 rebase
cd ~/pilamatch-t3-db-test
git fetch origin
git rebase origin/main

# 2. 마이그레이션 자동 생성
cd backend
alembic revision --autogenerate -m "add_payout_model_and_payment_fields"

# 3. 생성된 마이그레이션 파일 리뷰 (중요!)
# - payouts 테이블 생성 확인
# - payments 테이블에 새 컬럼 추가 확인
# - PaymentStatus에 REFUNDED 추가 확인

# 4. 마이그레이션 적용
alembic upgrade head
```

**주의사항:**
- `GUID()` 타입이 `CHAR(36)`으로 생성되는지 확인
- `String(20)` enum 컬럼이 올바른지 확인
- 기존 데이터에 nullable=True 또는 default 값 설정 필요

**프롬프트 예시:**
```
T1에서 추가한 Payout 모델과 Payment 필드에 대한 Alembic 마이그레이션을 생성해줘.
alembic revision --autogenerate -m "add_payout_model_and_payment_fields" 실행 후
생성된 파일을 리뷰하고 문제 있으면 수정해줘.
기존 payments 테이블의 새 컬럼은 nullable=True로 설정해야 해.
```

---

### #16 — OTP 저장소 Redis 이전 [HIGH]

**의존성:** T4-#22 (Redis 서비스 추가) 완료 후 작업

**문제:** OTP 코드가 메모리(dict)에 저장되어 서버 재시작 시 유실됨.

**수정 파일:**
- `backend/app/services/verification.py` — Redis 기반 OTP 저장

**수정 내용:**
```python
import redis.asyncio as redis

class VerificationService:
    def __init__(self, db, redis_client):
        self.db = db
        self.redis = redis_client

    async def send_otp(self, phone: str) -> str:
        otp = str(random.randint(100000, 999999))
        # Redis에 5분 TTL로 저장
        await self.redis.setex(f"otp:{phone}", 300, otp)
        return otp

    async def verify_otp(self, phone: str, code: str) -> bool:
        stored = await self.redis.get(f"otp:{phone}")
        if stored and stored.decode() == code:
            await self.redis.delete(f"otp:{phone}")
            return True
        return False
```

**프롬프트 예시:**
```
backend/app/services/verification.py의 OTP 저장을 메모리 dict에서 Redis로 이전해줘.
TTL 5분으로 설정하고, 검증 성공 시 즉시 삭제.
Redis 연결은 core/config.py의 REDIS_URL 사용.
```

---

### #17 — DB 커넥션 풀 설정 [MEDIUM]

**문제:** SQLAlchemy 커넥션 풀이 기본값으로 설정되어 있어 프로덕션에서 커넥션 부족 가능.

**수정 파일:**
- `backend/app/core/config.py` — 풀 설정 추가
- `backend/app/core/database.py` 또는 엔진 생성 부분 — 풀 파라미터 적용

**수정 내용:**
```python
# config.py에 추가
DB_POOL_SIZE: int = 10
DB_MAX_OVERFLOW: int = 20
DB_POOL_TIMEOUT: int = 30
DB_POOL_RECYCLE: int = 1800  # 30분

# 엔진 생성 시 적용
engine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=settings.DB_POOL_SIZE,
    max_overflow=settings.DB_MAX_OVERFLOW,
    pool_timeout=settings.DB_POOL_TIMEOUT,
    pool_recycle=settings.DB_POOL_RECYCLE,
    pool_pre_ping=True,
)
```

**프롬프트 예시:**
```
SQLAlchemy 엔진의 커넥션 풀 설정을 추가해줘.
config.py에 DB_POOL_SIZE=10, DB_MAX_OVERFLOW=20 등 환경변수 추가하고,
엔진 생성 시 pool_pre_ping=True도 설정해줘.
```

---

### #18 — 결제 플로우 E2E 테스트 [MEDIUM]

**의존성:** T1-#1,#2,#3 완료 후 작업

**문제:** 결제 관련 테스트가 없음.

**수정 파일:**
- `tests/test_payment.py` — 새 파일 생성

**테스트 케이스:**
```python
class TestPaymentFlow:
    async def test_initialize_payment(self):
        """결제 초기화 → order_id 발급"""
        pass

    async def test_confirm_payment(self):
        """Toss 결제 승인 → DB 상태 COMPLETED"""
        pass

    async def test_webhook_valid_signature(self):
        """유효한 서명의 webhook → 정상 처리"""
        pass

    async def test_webhook_invalid_signature(self):
        """잘못된 서명의 webhook → 403 반환"""
        pass

    async def test_refund(self):
        """환불 요청 → DB 상태 REFUNDED"""
        pass

    async def test_duplicate_payment(self):
        """중복 결제 시도 → 멱등성 처리"""
        pass

    async def test_payout_creation(self):
        """계약 완료 → Payout 자동 생성"""
        pass
```

**프롬프트 예시:**
```
tests/test_payment.py를 새로 만들어서 결제 플로우 E2E 테스트를 작성해줘.
결제 초기화, 승인, webhook, 환불, 중복 방지, payout 생성 테스트.
Toss API는 mock 처리하고, DB 상태 변화를 검증해줘.
```

---

### #19 — 계약 상태 전이 + 검증 테스트 [MEDIUM]

**문제:** 계약 상태 머신(CONFIRMED→IN_PROGRESS→COMPLETED/CANCELLED)에 대한 테스트 부족.

**수정 파일:**
- `tests/test_contracts.py` — 새 파일 또는 기존 파일에 추가

**테스트 케이스:**
```python
class TestContractStateMachine:
    async def test_valid_transition_confirmed_to_in_progress(self): ...
    async def test_valid_transition_in_progress_to_completed(self): ...
    async def test_valid_transition_in_progress_to_cancelled(self): ...
    async def test_invalid_transition_completed_to_in_progress(self): ...
    async def test_invalid_transition_cancelled_to_confirmed(self): ...
    async def test_event_log_created_on_transition(self): ...
    async def test_complete_contract_creates_payment(self): ...
```

**참고:** 상태 전이 규칙은 `backend/app/services/contract.py`의 `VALID_TRANSITIONS` dict 참조.

**프롬프트 예시:**
```
tests/test_contracts.py에 계약 상태 전이 테스트를 작성해줘.
contract.py의 VALID_TRANSITIONS에 따라 유효/무효 전이를 모두 테스트.
전이 시 contract_event_logs에 기록이 남는지도 확인.
```

---

### #20 — 보안 리뷰 실행 [LOW]

**의존성:** T1-#5 (CORS), T1-#6 (JWT), T1-#7 (Rate Limit) 완료 후 작업

**문제:** 전체 보안 점검이 필요.

**리뷰 범위:**
- `backend/app/core/security.py` — JWT 구현
- `backend/app/core/deps.py` — 인증/인가
- `backend/app/main.py` — CORS 설정
- `backend/app/services/payment.py` — 결제 보안
- `backend/app/api/v1/endpoints/auth.py` — 인증 API

**체크리스트:**
- [ ] JWT 시크릿 키 강도 확인
- [ ] 비밀번호 해싱 알고리즘 (bcrypt) 확인
- [ ] CORS 설정이 프로덕션에 적합한지
- [ ] SQL injection 취약점 없는지
- [ ] XSS 방지 (입력 검증)
- [ ] Rate limiting 적용 확인
- [ ] 결제 API에 인증 필수 확인
- [ ] 환경변수로 시크릿 관리 확인

**프롬프트 예시:**
```
security-reviewer 에이전트를 사용해서 전체 보안 리뷰를 실행해줘.
core/security.py, core/deps.py, main.py의 CORS, payment.py의 결제 로직,
auth.py의 인증 API를 중심으로 OWASP Top 10 기준으로 점검.
```

---

## 실행 순서 가이드

```
1라운드: #17 (커넥션 풀) + #19 (계약 테스트) — 독립, 즉시 가능
   ↓
2라운드: #15 (마이그레이션) — T1-#1,#2 머지 후
   ↓
3라운드: #18 (결제 테스트) — T1-#1,#2,#3 머지 후
   ↓
4라운드: #16 (OTP Redis) — T4-#22 완료 후
   ↓
5라운드: #20 (보안 리뷰) — T1-#5,#6,#7 완료 후
```

## 완료 체크리스트

- [ ] #15 마이그레이션이 `alembic upgrade head`로 정상 적용
- [ ] #16 OTP가 Redis에 저장되고 5분 후 자동 만료
- [x] #17 커넥션 풀 설정이 config에 반영
- [ ] #18 결제 테스트 7개 이상 PASS
- [x] #19 상태 전이 테스트 7개 이상 PASS
- [ ] #20 보안 리뷰 리포트 생성
