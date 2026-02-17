# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**PilaMatch** - Trust-based Pilates/Yoga instructor-studio matching platform MVP built with FastAPI + Streamlit.

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
open http://localhost:8501
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
- **Frontend**: Streamlit 1.30 (MVP)
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

frontend/
├── app.py                 # Streamlit UI (10+ screens)
└── api_client.py          # HTTP client wrapper
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
- Test auth flows
- Test state transitions
- Test payment webhooks
- Mock external services (SMS, payments)

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
| `frontend/app.py` | Streamlit UI entry point |
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

*Last updated: 2026-02-14*