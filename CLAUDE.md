# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**StudioBridge** - Trust-based Pilates/Yoga instructor-studio matching platform MVP built with FastAPI + Next.js.

### Core Values
- **신뢰 (Trust)**: Safety first - verified users, escrow payments, penalty system
- **Simple**: Focus on core features, avoid feature creep
- **Stable**: Stability > new features

### Current Status
✅ **MVP Complete** with all trust features implemented:
- Authentication with JWT
- Phone/business verification system
- 50k KRW deposit requirement
- Escrow payment system
- No-show penalty system (30k KRW penalty, 3-strike suspension)
- 4-factor matching algorithm
- Contract state machine with event logging
- Premium membership system (월 9,900원)

---

## Agent Delegation Rules

`.claude/agents/` 에 정의된 전문 에이전트를 작업 도메인에 따라 반드시 위임하라.

### 에이전트 → 도메인 매핑

| 에이전트 | 위임 조건 (해당 시 반드시 사용) |
|----------|-------------------------------|
| **backend-api** | API 엔드포인트, 라우터, 서비스 레이어, 미들웨어, `app/api/`, `app/services/` 하위 작업 |
| **database** | 스키마 변경, Alembic 마이그레이션, 쿼리 최적화, `app/models/` 수정, SQLAlchemy 관련 |
| **devops** | Docker, docker-compose, CI/CD, 배포 스크립트, 인프라 설정 |
| **doc-writer** | README, API 문서, `docs/` 하위 파일, 세션 요약 문서 작성 |
| **frontend-ui** | Next.js UI, `frontend-next/` 하위 코드, 화면 레이아웃, UX 개선 |
| **payment-trust** | 결제(Toss), 에스크로, 보증금, 패널티, `services/escrow.py`, `services/penalty.py`, `services/deposit.py` |
| **security-reviewer** | 인증/인가, JWT, CORS, 입력 검증, 보안 취약점 리뷰, `core/security.py`, `core/deps.py` |
| **test-qa** | 테스트 작성/수정, 커버리지 분석, `tests/` 하위 작업, pytest 실행 |
| **verify-app** | 앱 전체 동작 검증, 배포 전 체크, 서비스 헬스체크, 통합 검증 |

### 라우팅 판단 기준

- **단일 도메인 작업** → 해당 에이전트 1개에 위임
- **복합 작업** (예: 새 API + 테스트) → 순차 위임: backend-api → test-qa
- **코드 변경 후** → security-reviewer로 보안 리뷰 위임 고려
- **병렬 위임**: 도메인 간 파일 겹침이 없고 독립적일 때만

---

## Large File Handling Rules

- **25,000 토큰 초과 파일은 절대 한 번에 전체를 읽지 말 것**
- View tool 사용 시 반드시 `view_range` / `offset` / `limit` 파라미터로 범위 지정
- 큰 파일은 **Grep으로 필요한 부분을 먼저 검색**한 뒤, 해당 라인 범위만 읽을 것
- 생성된 파일(migration, lock 파일 등)은 전체를 읽을 필요 없음 — 변경된 부분만 확인
- 로그/데이터 파일은 `head`, `tail`, `grep` 등 bash 명령으로 처리

---

## Development Commands

### Quick Start
```bash
# Start all services (DB, Backend, Frontend)
docker-compose up -d --build

# View logs
docker-compose logs -f backend

# Reset database (WARNING: deletes all data)
docker-compose down -v && docker-compose up -d

# API Documentation
open http://localhost:8000/api/v1/docs

# Frontend
open http://localhost:3000
```

### Testing
```bash
cd backend
uv run pytest                          # Run all tests
uv run pytest tests/test_auth.py -v    # Run specific test
uv run pytest --cov=app                 # With coverage
```

### Database Operations
```bash
cd backend
alembic upgrade head      # Apply migrations
alembic revision --autogenerate -m "description"  # Create migration
```

---

## Architecture Overview

### System Flow
```
User Registration → Verification (SMS/Business) → Deposit → Service Usage
Job Posting → Matching Score → Application → Offer → Contract → Payment → Completion/Review
```

### Tech Stack
- **Backend**: FastAPI 0.109+ with async/await throughout
- **Database**: PostgreSQL (prod) / SQLite (test) via SQLAlchemy 2.0+
- **Frontend**: Next.js 15 (React)
- **Auth**: JWT tokens with HTTPBearer dependency
- **Package Manager**: uv (not pip)

### Project Structure
```
backend/
├── app/
│   ├── api/v1/endpoints/  # 13 REST routers
│   ├── services/          # 18 business logic services
│   ├── models/            # SQLAlchemy models with GUID type
│   ├── schemas/           # Pydantic validation
│   └── core/              # Config, security, deps
├── alembic/               # Database migrations
└── tests/                 # pytest test suite

frontend-next/
├── src/app/               # Next.js App Router pages
├── src/components/        # React components (shadcn/ui)
└── src/lib/               # API client, utilities
```

---

## Key Architectural Decisions

### 1. Database Compatibility Layer
```python
# Use GUID custom type instead of UUID for SQLite/PostgreSQL compatibility
from app.models.base import GUID  # maps to CHAR(36)

# Use String(20) for enums, not SQLEnum
role = Column(String(20), nullable=False)  # 'instructor' | 'studio'

# Use JSON for arrays instead of ARRAY type
certifications = Column(JSON, default=list)
```

### 2. State Machine Pattern
Contract transitions are strictly validated with event logging:
```python
VALID_TRANSITIONS = {
    CONFIRMED: {IN_PROGRESS, CANCELLED},
    IN_PROGRESS: {COMPLETED, CANCELLED},
    COMPLETED: set(),    # Terminal
    CANCELLED: set(),    # Terminal
}
```

### 3. Matching Algorithm (backend/app/services/matching.py)
4-factor weighted scoring (0-100):
- Region match: 30%
- Experience: 25%
- Certifications: 25%
- Hourly rate: 20%

### 4. Trust Features Implementation
- **Verification**: `services/verification.py` - Phone OTP (dev mode returns code)
- **Deposit**: `services/deposit.py` - 50k KRW requirement
- **Escrow**: `services/escrow.py` - Payment held until completion
- **Penalties**: `services/penalty.py` - No-show tracking & suspension

---

## API Patterns

### Authentication
```python
from app.core.deps import get_current_user, require_role
from app.models import UserRole

@router.post("/endpoint")
async def endpoint(
    current_user: User = Depends(get_current_user),  # Any authenticated user
    # OR
    current_user: User = Depends(require_role(UserRole.STUDIO))  # Role-specific
):
    pass
```

### Error Responses
```python
raise HTTPException(
    status_code=400,
    detail={"code": "ERROR_CODE", "message": "Human readable message"}
)
```

### Service Layer Pattern
```python
# Endpoint → Service → Database
@router.post("/contracts")
async def create_contract(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = ContractService(db)
    return await service.create_from_offer(...)
```

---

## Testing Workflow

### 테스트 피드백 루프 (필수)

> **Claude에게 작업을 검증할 방법을 제공하는 것이 최종 결과물 품질을 2~3배 높이는 가장 중요한 요소다.**

모든 기능 구현은 다음 루프를 따른다:
```
구현 → 테스트 작성 → 실행 → 실패 시 수정 → 재실행 → 통과 시 커밋
```

### 변경 대상별 테스트 실행 규칙

| 변경 대상 | 필수 테스트 | 명령어 |
|-----------|------------|--------|
| `app/services/` | 단위 테스트 | `uv run pytest tests/test_{service}.py -v` |
| `app/api/` | API 통합 테스트 | `uv run pytest tests/test_{endpoint}.py -v` |
| `app/models/` | 스키마 + 전체 | `uv run pytest --cov=app` |
| `services/escrow.py`, `penalty.py`, `deposit.py` | 결제/신뢰 (필수) | `uv run pytest tests/test_payment*.py tests/test_penalty*.py -v` |
| `core/security.py`, `core/deps.py` | 보안 테스트 | `uv run pytest tests/test_auth.py -v` |
| `frontend-next/` | 수동 브라우저 검증 | DevTools 모바일 뷰 확인 |

### 테스트 우선순위

```
P0 (반드시 테스트):
  - 회원가입/로그인 인증 플로우
  - 보증금 입금/차감
  - 에스크로 결제 → 완료 → 정산
  - 노쇼 패널티 → 3회 정지
  - 계약 상태 전이 (state machine)

P1 (기능 완성 시 테스트):
  - 매칭 알고리즘 점수 계산
  - 프리미엄 멤버십 혜택 적용
  - 일일 사용량 제한/리셋

P2 (시간 여유 시):
  - 프로필 CRUD
  - 공고 목록 정렬/필터
  - 리뷰 작성
```

### 테스트 실패 시 행동 규칙

```
1. 에러 메시지 읽고 원인 분석
2. 테스트가 잘못된 경우 → 테스트 수정
3. 코드가 잘못된 경우 → 코드 수정
4. 수정 후 반드시 재실행 (최대 3회 반복)
5. 3회 후에도 실패 → 원인과 시도한 방법을 정리하여 사용자에게 보고
```

### E2E 테스트 (Playwright)

```bash
uv add --dev pytest-playwright
uv run playwright install chromium
uv run pytest tests/e2e/ -v
```

E2E 대상 (크리티컬 플로우만):
1. 회원가입 → 인증 → 보증금 입금 → 서비스 이용 가능
2. 공고 작성 → 매칭 → 지원 → 오퍼 → 계약 → 결제 → 완료
3. 노쇼 신고 → 패널티 → 보증금 차감 → 3회 시 계정 정지
4. 프리미엄 구독 → 혜택 적용 확인

---

## Development Rules

### 1. Session Documentation
When session reaches 80% capacity, create `docs/summary_YYYYMMDD.md` with:
- Features implemented
- Issues resolved
- Schema changes
- Next steps TODO
- How to run

### 2. Code Standards
- **Always use type hints** on all functions
- **Async/await** for all I/O operations
- **No hardcoded secrets** - use environment variables
- **Validate state transitions** - never skip validation
- **Log all state changes** to event tables

### 3. Git Commits
```
feat: New feature
fix: Bug fix
docs: Documentation
refactor: Code refactoring
test: Test changes
```

### 4. Testing Requirements
- 모든 기능 구현 후 반드시 관련 테스트 작성 및 통과 확인
- 결제/신뢰 관련 변경 시 `/test-payment` 필수 실행
- PR 생성 전 `/test-and-fix` 필수 실행
- 커버리지: 핵심 서비스 80%+, 전체 60%+
- 필수 케이스: Happy path + 엣지케이스 + 에러 케이스 (최소 3개)
- Mock 대상: SMS API, 토스페이먼츠 API, 국세청 API
- 테스트 통과 전 커밋 금지

---

## Common Tasks

### Add New API Endpoint
1. Create router in `backend/app/api/v1/endpoints/`
2. Add service in `backend/app/services/`
3. Create schemas in `backend/app/schemas/`
4. Register router in `backend/app/api/v1/router.py`
5. Write tests in `backend/tests/`

### Modify Database Schema
1. Edit model in `backend/app/models/`
2. Create migration: `alembic revision --autogenerate -m "description"`
3. Review migration file
4. Apply: `alembic upgrade head`

### Handle Payment Webhook
See `backend/app/api/v1/endpoints/payments.py:handle_webhook()` for idempotent processing pattern.

### Add Verification Check
Use `backend/app/services/verification.py` methods and check `user.phone_verified` or `user.business_verified`.

---

## Environment Variables

### Required
```bash
DATABASE_URL=postgresql+asyncpg://user:pass@host/db
DATABASE_URL_SYNC=postgresql://user:pass@host/db  # For Alembic
SECRET_KEY=your-secret-key-change-in-production
```

### External Services (Production)
```bash
TOSS_CLIENT_KEY=live_ck_...
TOSS_SECRET_KEY=live_sk_...
SMS_API_KEY=...  # NHN Cloud
BUSINESS_API_KEY=...  # 국세청
```

---

## Premium Membership System (v3.0)

### 프리미엄 멤버십 정의 (월 9,900원)

#### 공통 혜택 (강사 & 스튜디오):
1. **💰 플랫폼 수수료 40% 할인**
   - 무료 회원: 계약 완료 시 5% 수수료
   - 프리미엄 회원: 계약 완료 시 3% 수수료 (계약당 2% 절약)
   - 구현: `backend/app/services/contract.py:_get_fee_rate()`

2. **🏆 프리미엄 배지 + Trust Score +10점**
   - 프로필에 프리미엄 배지 표시 (has_premium_badge 필드)
   - Trust Score 10점 추가 (5점에서 상향)
   - 신뢰도 레벨 상승 효과
   - 구현: `backend/app/services/trust_score.py` (line 229)

#### 강사 전용 혜택:
1. **🚀 무제한 일일 지원**
   - 무료 회원: 하루 5회 지원 제한
   - 프리미엄 회원: 무제한 지원 가능
   - 구현: `backend/app/services/daily_usage.py`, `backend/app/services/application.py`

2. **📈 매칭 점수 30% 부스트**
   - 모든 매칭 점수에 1.3배 자동 적용 (최대 100점)
   - 스튜디오에게 더 높은 점수로 노출
   - 구현: `backend/app/services/matching.py:calculate_matching_score(is_premium=True)`

3. **📝 지원서 템플릿 10개 저장**
   - 자주 사용하는 지원서 내용을 템플릿으로 저장
   - 빠른 지원을 위한 맞춤 템플릿 관리
   - 구현: `backend/app/services/application_template.py` (프리미엄 전용)

#### 스튜디오 전용 혜택:
1. **👀 무제한 강사 프로필 열람**
   - 무료 회원: 하루 5명 열람 제한
   - 프리미엄 회원: 무제한 열람
   - 구현: `backend/app/services/daily_usage.py:track_profile_view()`
   - API: `GET /api/v1/instructors/{instructor_id}`

2. **⭐ 공고 우선 노출**
   - 강사들에게 상단 우선 표시
   - 프리미엄 공고가 항상 먼저 노출
   - 구현: `backend/app/services/job_post.py:list()` (premium_first=True)

3. **📊 프리미엄 강사 우선 매칭**
   - 프리미엄 강사 지원 시 우선 정렬
   - 구현: `backend/app/api/v1/endpoints/applications.py` (line 120)

### 일일 사용 제한 시스템:
- **데이터베이스**: `daily_usage_limits` 테이블
- **리셋 시간**: 매일 자정
- **추적 필드**:
  - `daily_applications_today` - 오늘 지원 횟수
  - `daily_views_today` - 오늘 열람 횟수
  - `last_usage_reset_date` - 마지막 리셋 날짜
  - `last_viewed_profiles` - 오늘 열람한 프로필 ID 목록

### 관련 파일:
- `backend/app/services/subscription.py` - 구독 관리 서비스
- `backend/app/services/daily_usage.py` - 일일 사용량 추적 서비스
- `backend/app/models/daily_usage.py` - 일일 사용량 모델
- `backend/app/models/subscription.py` - 구독 데이터 모델
- `backend/app/api/v1/endpoints/subscription.py` - 구독 API
- `backend/app/api/v1/endpoints/usage.py` - 사용량 조회 API
- `frontend-next/src/app/` - 프리미엄 UI (역할별 혜택 표시)

---

## Debugging Tips

### Check Contract State
```python
# View contract with all transitions
SELECT c.*, cel.* FROM contracts c
JOIN contract_event_logs cel ON c.id = cel.contract_id
WHERE c.id = 'uuid'
ORDER BY cel.created_at;
```

### Test Matching Score
```python
from app.services.matching import calculate_matching_score
score = calculate_matching_score(instructor_profile, job_post)
print(score)  # {"total": 85, "breakdown": {...}}
```

### Simulate No-Show
```python
POST /api/v1/contracts/{id}/report-no-show
# Automatically: penalty applied, deposit deducted, contract cancelled
```

---

## Important Files Reference

| File | Purpose |
|------|---------|
| `backend/app/services/contract.py` | State machine implementation |
| `backend/app/services/matching.py` | Matching algorithm |
| `backend/app/services/penalty.py` | No-show penalty logic |
| `backend/app/models/base.py` | GUID type, mixins |
| `backend/app/core/deps.py` | Auth dependencies |
| `backend/app/core/security.py` | JWT, password hashing |
| `frontend-next/` | Next.js frontend |
| `docker-compose.yml` | Service orchestration |

---

## Production Checklist

- [ ] Change SECRET_KEY
- [ ] Set DEBUG=false
- [ ] Configure real SMS service
- [ ] Configure real payment keys
- [ ] Set up monitoring (Sentry)
- [ ] Configure backup strategy
- [ ] Review CORS settings
- [ ] Set up rate limiting

---

*Last updated: 2026-02-18*