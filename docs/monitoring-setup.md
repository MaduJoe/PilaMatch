# Monitoring Setup

## Sentry

### Backend (FastAPI)

```bash
cd backend
uv add sentry-sdk[fastapi]
```

`app/main.py`에 추가:
```python
import sentry_sdk

if settings.SENTRY_DSN:
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        traces_sample_rate=0.1,
        profiles_sample_rate=0.1,
        environment=settings.APP_ENV,
    )
```

### Frontend (Next.js)

```bash
cd frontend-next
npm install @sentry/nextjs
npx @sentry/wizard@latest -i nextjs
```

### 환경변수

```bash
SENTRY_DSN=https://xxx@xxx.ingest.sentry.io/xxx
```

---

## Structured Logging

### 설치

```bash
cd backend
uv add structlog
```

### Request ID Tracing

`X-Request-ID` 헤더 미들웨어를 추가하여 요청별 추적:

```python
import uuid
from starlette.middleware.base import BaseHTTPMiddleware

class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response
```

### structlog 설정

```python
import structlog

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.dev.ConsoleRenderer()  # 프로덕션: JSONRenderer()
    ],
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
)
```

---

## Docker 로그 관리

`docker-compose.prod.yml`에 이미 로그 로테이션 설정됨:

```yaml
logging:
  driver: json-file
  options:
    max-size: "10m"
    max-file: "3"
```

---

## Health Check

프로덕션 헬스체크 엔드포인트: `GET /api/v1/health`

`docker-compose.prod.yml`에서 30초 간격으로 체크:

```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
  interval: 30s
  timeout: 10s
  retries: 3
```
