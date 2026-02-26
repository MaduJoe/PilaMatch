# INFRA Worktree — 작업 지시서

> **브랜치**: `feat/infra`
> **수정 범위**: `docker-compose.yml`, `backend/entrypoint.sh`, `.github/`, `tests/`, `docs/`, `.env.example`, `pyproject.toml`
> **수정 금지**: `backend/app/api/` (BACKEND 전용), `backend/app/models/` (DATA 전용), `frontend-next/src/` (FRONTEND 전용)
> **규칙**: 인프라 변경 후 `docker-compose config` 검증. 각 작업 완료 후 git commit.

---

## Task 1: 법적 문서 작성 (Phase 1 — BLOCKER)

### 1-1. 개인정보처리방침 (한국어)

파일: `docs/privacy-policy-ko.md` (신규)

PIPA(개인정보보호법) 필수 항목 포함:
```
1. 개인정보의 수집 및 이용 목적
2. 수집하는 개인정보 항목
   - 필수: 이메일, 비밀번호(해시), 이름, 전화번호
   - 선택: 프로필 사진, 경력사항
   - 사업자: 사업자등록번호, 상호명
   - 자동수집: 접속 IP, 기기정보, 접속 일시
3. 개인정보 보유 및 이용 기간
   - 회원탈퇴 후 30일 (법정 의무보관 항목 제외)
   - 전자상거래법: 계약/결제 기록 5년, 소비자 불만 3년
4. 개인정보의 제3자 제공
   - TossPayments (결제 처리)
   - CoolSMS (SMS 인증)
5. 개인정보의 파기 절차 및 방법
6. 이용자의 권리와 행사 방법
7. 개인정보 보호책임자
8. 개인정보 처리방침 변경에 관한 사항
```

### 1-2. 이용약관 (한국어)

파일: `docs/terms-of-service-ko.md` (신규)

```
1. 목적
2. 용어 정의 (강사, 스튜디오, 매칭, 계약, 에스크로 등)
3. 서비스의 제공 및 변경
4. 회원가입 및 관리
5. 회원의 의무
6. 금지행위 (허위 정보, 노쇼 악용, 부정 리뷰 등)
7. 결제 및 환불
   - 에스크로 결제 방식 설명
   - 환불 조건 (계약 전/중/후)
   - 프리미엄 구독 환불
8. 보증금 제도
9. 노쇼 패널티 (30,000원 차감, 3회 정지)
10. 분쟁 해결
11. 면책 조항
12. 계정 정지 및 해지
13. 준거법 및 관할법원
14. 시행일
```

### 1-3. 환불정책

파일: `docs/refund-policy.md` (신규, 한/영 병기)

```
에스크로 환불:
- 계약 시작 전: 전액 환불
- 계약 진행 중: 쌍방 협의 후 비율 환불
- 계약 완료 후: 환불 불가 (분쟁 제외)

프리미엄 구독 환불:
- 결제 후 7일 이내: 전액 환불
- 7일 이후: 남은 기간 일할 계산

분쟁 기반 환불:
- 운영자 중재 → 증거 기반 판정 → 환불 또는 기각
```

### 1-4. 영문 버전

파일: `docs/privacy-policy-en.md`, `docs/terms-of-service-en.md` (신규)
- 한국어 문서의 영문 번역

커밋: `docs: 개인정보처리방침, 이용약관, 환불정책 (한/영)`

---

## Task 2: entrypoint.sh 프로덕션 대응 (Phase 4)

파일: `backend/entrypoint.sh` 수정

```bash
# 기존: uvicorn ... --reload (개발 전용)
# 변경: 환경변수 기반 분기

if [ "$APP_ENV" = "production" ]; then
    uvicorn app.main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --workers ${WORKERS:-4} \
        --loop uvloop \
        --no-access-log
else
    uvicorn app.main:app \
        --host 0.0.0.0 \
        --port 8000 \
        --reload
fi
```

커밋: `fix: entrypoint.sh 프로덕션/개발 모드 분리`

---

## Task 3: Docker Compose 프로덕션 분리 (Phase 4)

### 3-1. docker-compose.override.yml (개발 전용)

파일: `docker-compose.override.yml` (신규)

```yaml
# 개발 환경 전용 설정 (docker-compose up 시 자동 적용)
services:
  backend:
    volumes:
      - ./backend:/app  # 핫 리로드용
    environment:
      - APP_ENV=development
```

### 3-2. docker-compose.prod.yml

파일: `docker-compose.prod.yml` (신규)

```yaml
# docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
services:
  backend:
    environment:
      - APP_ENV=production
      - WORKERS=4
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: '1.0'
    restart: always
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/v1/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    logging:
      driver: json-file
      options:
        max-size: "10m"
        max-file: "3"

  db:
    restart: always
    volumes:
      - postgres_data:/var/lib/postgresql/data

  frontend:
    restart: always
```

### 3-3. 기존 docker-compose.yml에서 개발 전용 설정 제거

파일: `docker-compose.yml` 수정
- `volumes: ./backend:/app` → override로 이동
- 핫 리로드 관련 설정 → override로 이동

커밋: `chore: Docker Compose 개발/프로덕션 분리`

---

## Task 4: .env.example 완성 (Phase 4)

파일: `.env.example` 수정 (기존 28줄 → 전체)

```bash
# ─── App ───
APP_ENV=development          # development / production
DEBUG=true
SECRET_KEY=change-me-in-production
WORKERS=4

# ─── Database ───
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/pilamatch
DATABASE_URL_SYNC=postgresql://postgres:postgres@db:5432/pilamatch
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=pilamatch

# ─── CORS ───
CORS_ORIGINS=http://localhost:3000,http://localhost:8000

# ─── JWT ───
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7

# ─── SMS (CoolSMS) ───
SMS_API_KEY=
SMS_API_SECRET=
SMS_SENDER_NUMBER=

# ─── Payment (TossPayments) ───
TOSS_CLIENT_KEY=
TOSS_SECRET_KEY=

# ─── Business Verification (국세청) ───
NTS_API_KEY=

# ─── Email ───
EMAIL_PROVIDER=mock          # mock / smtp / sendgrid
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASSWORD=

# ─── File Upload ───
STORAGE_BACKEND=local        # local / s3
S3_BUCKET=
S3_REGION=
S3_ACCESS_KEY=
S3_SECRET_KEY=
UPLOAD_MAX_SIZE_MB=10

# ─── Push Notification ───
FCM_SERVER_KEY=

# ─── Monitoring ───
SENTRY_DSN=
```

커밋: `chore: .env.example 전체 환경변수 문서화`

---

## Task 5: 헬스체크 강화 (Phase 4)

파일: 확인 필요 — 기존 health 엔드포인트가 있으면 수정, 없으면 별도 요청

헬스체크가 BE worktree 범위일 수 있으므로, 여기서는 Docker healthcheck 설정만 담당.
docker-compose.prod.yml에 이미 포함됨 (Task 3).

커밋: (Task 3에 포함)

---

## Task 6: CI/CD 파이프라인 (Phase 4)

### 6-1. CI 워크플로우

파일: `.github/workflows/ci.yml` (신규)

```yaml
name: CI
on:
  push:
    branches: [main, feat/*]
  pull_request:
    branches: [main]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: cd backend && uv sync
      - run: cd backend && uv run ruff check .

  test:
    runs-on: ubuntu-latest
    needs: lint
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: cd backend && uv sync
      - run: cd backend && uv run pytest --cov=app --cov-report=xml -q
      - uses: codecov/codecov-action@v4
        with:
          file: backend/coverage.xml

  build:
    runs-on: ubuntu-latest
    needs: test
    steps:
      - uses: actions/checkout@v4
      - run: docker compose build
```

커밋: `ci: GitHub Actions CI 파이프라인 (lint + test + build)`

---

## Task 7: Sentry 연동 준비 (Phase 4)

파일: `backend/app/core/config.py`에 추가할 내용 메모 (BE worktree 범위이므로 여기서는 문서만)

파일: `docs/monitoring-setup.md` (신규)

```markdown
# Monitoring Setup

## Sentry
- Backend: `pip install sentry-sdk[fastapi]`
- `app/main.py`에 `sentry_sdk.init(dsn=settings.SENTRY_DSN)` 추가
- Frontend: `npm install @sentry/nextjs`

## Structured Logging
- `pip install structlog` 또는 `python-json-logger`
- Request ID tracing: X-Request-ID 헤더 미들웨어
```

커밋: `docs: 모니터링 셋업 가이드`

---

## Task 8: 스토어 설명문 (Phase 2)

### 8-1. 한국어

파일: `docs/store-description-ko.md` (신규)

```
앱 이름: PilaMatch
부제: 신뢰 기반 필라테스/요가 강사 매칭

설명:
PilaMatch는 검증된 필라테스/요가 강사와 스튜디오를 안전하게 연결하는 매칭 플랫폼입니다.

주요 기능:
• 본인인증 + 사업자인증으로 검증된 회원만 참여
• AI 기반 4요소 매칭 알고리즘 (지역, 경력, 자격, 급여)
• 에스크로 결제로 안전한 거래
• 노쇼 패널티 시스템으로 신뢰 보장
• Trust Score로 신뢰도 한눈에 확인

카테고리: 비즈니스 / 건강 및 피트니스
```

### 8-2. 영어

파일: `docs/store-description-en.md` (신규)

커밋: `docs: 앱스토어 설명문 (한/영)`

---

## 작업 순서 요약

```
Task 1 (법적 문서) → Task 2 (entrypoint) → Task 3 (Docker 분리) → Task 4 (.env.example)
→ Task 5 (헬스체크) → Task 6 (CI/CD) → Task 7 (모니터링 문서) → Task 8 (스토어 설명)
```

각 Task 완료 후:
1. Docker 관련: `docker-compose config` (또는 `docker compose config`) 로 문법 검증
2. CI 관련: YAML 문법 확인
3. git commit
