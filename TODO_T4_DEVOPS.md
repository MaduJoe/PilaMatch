# T4: DevOps + Docs — TODO

## 이 터미널의 역할

Docker, docker-compose, CI/CD 파이프라인, 배포, 환경설정, 문서 작업 담당.

**담당 파일 범위:**
- `docker-compose.yml` — 서비스 오케스트레이션
- `backend/Dockerfile` — 백엔드 이미지
- `frontend/Dockerfile` — 프론트엔드 이미지
- `.github/workflows/` — CI/CD
- `docs/` — 문서
- `.env*` — 환경변수 파일

**CLAUDE.md 에이전트:** `devops`, `doc-writer`

---

## TODO 목록

| # | 우선순위 | 작업 | 의존성 |
|---|---------|------|--------|
| 21 | CRITICAL | docker-compose 보안 강화 | - |
| 22 | HIGH | Redis 서비스 추가 | - |
| 23 | HIGH | Dockerfile 최적화 + 보안 | - |
| 24 | MEDIUM | GitHub Actions CI/CD | - |
| 25 | MEDIUM | 모니터링 + 구조화 로깅 | - |
| 26 | LOW | .env.example 정리 | - |

---

## 작업 상세

### #21 — docker-compose 보안 강화 [CRITICAL]

**문제:** `docker-compose.yml`에 하드코딩된 비밀번호와 시크릿 키가 있음.

**수정 파일:**
- `docker-compose.yml:4-7` — PostgreSQL 자격증명 하드코딩
- `docker-compose.yml:25-28` — backend 환경변수 하드코딩

**현재 문제 (docker-compose.yml):**
```yaml
# Line 4-7: 하드코딩된 DB 자격증명
POSTGRES_USER: postgres
POSTGRES_PASSWORD: password      # 위험!
POSTGRES_DB: quicksam

# Line 25-28: 하드코딩된 시크릿
DATABASE_URL=...postgres:password@...  # 위험!
SECRET_KEY=your-secret-key-change-in-production  # 위험!
DEBUG=true  # 프로덕션에서 위험!
```

**수정 내용:**
```yaml
services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-postgres}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:?POSTGRES_PASSWORD is required}
      POSTGRES_DB: ${POSTGRES_DB:-quicksam}
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-postgres}"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    depends_on:
      db:
        condition: service_healthy
    environment:
      DATABASE_URL: postgresql+asyncpg://${POSTGRES_USER:-postgres}:${POSTGRES_PASSWORD}@db:5432/${POSTGRES_DB:-quicksam}
      SECRET_KEY: ${SECRET_KEY:?SECRET_KEY is required}
      DEBUG: ${DEBUG:-false}
```

**프롬프트 예시:**
```
docker-compose.yml의 하드코딩된 비밀번호와 시크릿 키를 환경변수 참조로 바꿔줘.
${VAR:?error} 문법으로 필수값은 에러 발생시키고, 선택값은 ${VAR:-default} 사용.
db 서비스에 healthcheck 추가하고, backend는 db healthy 조건으로 depends_on 설정해줘.
DEBUG는 기본값 false로 설정.
```

---

### #22 — Redis 서비스 추가 [HIGH]

**문제:** JWT 블랙리스트(T1-#6), OTP 저장(T3-#16), 캐싱에 Redis가 필요.

**수정 파일:**
- `docker-compose.yml` — Redis 서비스 추가
- `backend/app/core/config.py` — REDIS_URL 설정

**수정 내용:**
```yaml
# docker-compose.yml에 추가
  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    command: redis-server --appendonly yes --maxmemory 256mb --maxmemory-policy allkeys-lru

  backend:
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
    environment:
      REDIS_URL: redis://redis:6379/0

volumes:
  postgres_data:
  redis_data:
```

```python
# config.py에 추가
REDIS_URL: str = "redis://localhost:6379/0"
```

**프롬프트 예시:**
```
docker-compose.yml에 Redis 서비스를 추가해줘.
redis:7-alpine 이미지, appendonly 활성화, maxmemory 256mb.
healthcheck 추가하고 backend가 redis healthy 후 시작하도록 depends_on 설정.
config.py에 REDIS_URL 환경변수도 추가해줘.
```

---

### #23 — Dockerfile 최적화 + 보안 [HIGH]

**문제:** backend/frontend Dockerfile이 root로 실행되고, 레이어 캐싱이 비효율적.

**수정 파일:**
- `backend/Dockerfile:1-27` — non-root 유저, 멀티스테이지 빌드
- `frontend/Dockerfile:1-17` — non-root 유저

**Backend Dockerfile 수정:**
```dockerfile
FROM python:3.11-slim AS builder
WORKDIR /build
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.11-slim
WORKDIR /app

# non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

COPY --from=builder /install /usr/local
COPY . .

RUN chown -R appuser:appuser /app
USER appuser

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/health')"

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Frontend Dockerfile 수정:**
```dockerfile
FROM python:3.11-slim
WORKDIR /app

RUN groupadd -r appuser && useradd -r -g appuser appuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN chown -R appuser:appuser /app
USER appuser

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8501/_stcore/health')"

EXPOSE 8501
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

**프롬프트 예시:**
```
backend/Dockerfile과 frontend/Dockerfile을 최적화해줘.
1) non-root 유저(appuser)로 실행
2) backend는 멀티스테이지 빌드로 이미지 크기 줄이기
3) HEALTHCHECK 추가
4) pip --no-cache-dir로 캐시 제거
```

---

### #24 — GitHub Actions CI/CD [MEDIUM]

**문제:** CI/CD 파이프라인이 없음.

**수정 파일:**
- `.github/workflows/ci.yml` — 새 파일 생성

**수정 내용:**
```yaml
name: CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test_quicksam
        ports: [5432:5432]
        options: --health-cmd pg_isready --health-interval 10s --health-timeout 5s --health-retries 5
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install uv && uv pip install -r requirements.txt
      - run: uv run pytest --cov=app --cov-report=xml
        env:
          DATABASE_URL: postgresql+asyncpg://postgres:test@localhost:5432/test_quicksam

  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: pip install ruff && ruff check backend/

  docker:
    needs: [test, lint]
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: docker compose build
```

**프롬프트 예시:**
```
.github/workflows/ci.yml을 만들어서 CI/CD 파이프라인을 구성해줘.
test job: PostgreSQL 서비스 + pytest, lint job: ruff, docker job: 빌드 확인.
main 브랜치 push와 PR에 트리거.
```

---

### #25 — 모니터링 + 구조화 로깅 [MEDIUM]

**문제:** 로깅이 print 기반이고, 모니터링이 없음.

**수정 파일:**
- `backend/app/core/logging.py` — 새 파일, structlog 설정
- `backend/app/main.py` — 로깅 미들웨어 추가

**수정 내용:**
```python
# logging.py
import structlog

def setup_logging():
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.PrintLoggerFactory(),
    )

# main.py에 미들웨어 추가
@app.middleware("http")
async def log_requests(request, call_next):
    logger = structlog.get_logger()
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    logger.info("request",
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        duration_ms=round(duration * 1000),
    )
    return response
```

**프롬프트 예시:**
```
structlog를 사용해서 구조화 로깅을 설정해줘.
core/logging.py에 setup_logging() 함수 만들고,
main.py에 HTTP 요청 로깅 미들웨어 추가.
JSON 형식으로 method, path, status, duration 기록.
```

---

### #26 — .env.example 정리 [LOW]

**문제:** `.env.example` 파일이 실제 필요한 환경변수와 동기화되지 않음.

**수정 파일:**
- `backend/.env.example` — 업데이트

**수정 내용:**
```bash
# Database
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/quicksam
DATABASE_URL_SYNC=postgresql://postgres:password@localhost:5432/quicksam

# Security
SECRET_KEY=change-me-in-production-use-openssl-rand-hex-32
DEBUG=false

# Redis
REDIS_URL=redis://localhost:6379/0

# Toss Payments
TOSS_CLIENT_KEY=test_ck_...
TOSS_SECRET_KEY=test_sk_...
TOSS_WEBHOOK_SECRET=...

# External APIs (Production)
SMS_API_KEY=
BUSINESS_API_KEY=

# CORS
ALLOWED_ORIGINS=http://localhost:8501

# Database Pool
DB_POOL_SIZE=10
DB_MAX_OVERFLOW=20
```

**프롬프트 예시:**
```
backend/.env.example을 현재 codebase에서 실제 사용하는 환경변수에 맞게 업데이트해줘.
각 변수에 설명 주석을 달고, 기본값은 개발 환경 기준으로 설정.
SECRET_KEY는 "change-me" 같은 플레이스홀더 사용.
```

---

## 실행 순서 가이드

```
1라운드: #21 (docker-compose 보안) + #22 (Redis) — 병렬 가능
   ↓
2라운드: #23 (Dockerfile 최적화) — #21 참고
   ↓
3라운드: #24 (CI/CD) + #25 (로깅) — 병렬 가능
   ↓
4라운드: #26 (.env.example) — 모든 환경변수 확정 후
```

## 완료 체크리스트

- [x] #21 docker-compose에 하드코딩된 시크릿이 0개
- [x] #22 `docker-compose up`으로 Redis 정상 기동, `redis-cli ping` → PONG
- [x] #23 컨테이너가 non-root(appuser)로 실행
- [x] #24 GitHub Actions에서 테스트/린트/빌드 통과
- [x] #25 요청 로그가 JSON 형식으로 출력
- [x] #26 .env.example에 모든 필수 변수 포함
