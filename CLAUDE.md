# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**PilaMatch** - Trust-based Pilates/Yoga instructor-studio matching platform MVP (FastAPI + Next.js)

### Core Values
- **신뢰 (Trust)**: Safety first - verified users, Trust Score, penalty system
- **Simple**: Focus on core features, avoid feature creep
- **Stable**: Stability > new features

**Current Status**: MVP Complete (인증, 매칭, 계약, Tier, 패널티, 직접 정산, Premium 비활성)

---

## Agent Delegation Rules

`.claude/agents/`에 정의된 전문 에이전트를 작업 도메인에 따라 반드시 위임하라.

| 에이전트 | 위임 조건 (해당 시 반드시 사용) |
|----------|-------------------------------|
| **backend-api** | API 엔드포인트, 라우터, 서비스 로직, `app/api/`, `app/services/` 하위 작업 |
| **database** | 스키마 변경, Alembic 마이그레이션, 쿼리 최적화, `app/models/` 수정 |
| **frontend-ui** | Next.js UI, `frontend-next/` 하위 코드, UX 개선 |
| **test-qa** | 테스트 작성/수정, 커버리지 분석, `tests/` 하위 작업 |
| **payment-trust** | 직접 정산, Tier 등급, 패널티, Trust Score, 구독 관련 서비스 |
| **security-reviewer** | 인증/인가, JWT, 보안 취약점 리뷰 (읽기 전용) |
| **devops** | Docker, CI/CD, 배포, 인프라 설정 |
| **doc-writer** | README, API 문서, `docs/` 하위 파일, 세션 요약 |

### 라우팅 판단 기준
- **단일 도메인** → 해당 에이전트 1개에 위임
- **복합 작업** → 순차 위임 (예: backend-api → test-qa)
- **코드 변경 후** → security-reviewer 보안 리뷰 고려
- **병렬 위임**: 도메인 간 파일 겹침 없고 독립적일 때만

---

## Large File Handling Rules

- **25,000 토큰 초과 파일은 절대 한 번에 전체를 읽지 말 것**
- 큰 파일은 Grep으로 필요한 부분 먼저 검색 후 해당 라인만 읽을 것
- 생성된 파일(migration, lock 파일 등)은 변경된 부분만 확인

---

## Development Commands

```bash
# Start all services
docker-compose up -d --build

# View logs
docker-compose logs -f backend

# Reset database (WARNING: deletes all data)
docker-compose down -v && docker-compose up -d

# Testing
cd backend
uv run pytest                          # Run all tests
uv run pytest tests/test_auth.py -v    # Run specific test
uv run pytest --cov=app                # With coverage

# Database migrations
cd backend
alembic upgrade head
alembic revision --autogenerate -m "description"
```

---

## Tech Stack

- **Backend**: FastAPI 0.109+ / SQLAlchemy 2.0 (async) / PostgreSQL (prod) / SQLite (test)
- **Frontend**: Next.js 15 (App Router) / TypeScript / Tailwind CSS / shadcn/ui
- **Auth**: JWT (HTTPBearer) / **Package Manager**: uv (not pip)

---

## Code Standards

- **Always use type hints** on all functions
- **Async/await** for all I/O operations
- **No hardcoded secrets** - use environment variables
- **Validate state transitions** - never skip validation
- **Log all state changes** to event tables
- **테스트 피드백 루프**: 구현 → 테스트 작성 → 실행 → 통과 → 커밋

### Git Commits
```
feat: New feature    fix: Bug fix       docs: Documentation
refactor: Refactoring    test: Test changes
```

---

## Workflow Discipline

### Hooks (자동 가드레일)
`.claude/hooks/`에 3개의 자동 가드레일:
- **prompt-guard.sh** (UserPromptSubmit): 모호한 프롬프트 차단
- **write-guard.sh** (PreToolUse: Write|Edit): 허용 디렉토리 외 파일 생성 차단
- **post-write.sh** (PostToolUse: Write|Edit): 코드 수정 후 테스트 리마인더

### Plan Mode vs 직접 구현
Plan Mode 또는 /dev: 3개+ 파일 수정, 새 파일 생성, 복수 도메인, 불확실한 범위
직접 구현 OK: 단일 파일, 명확한 범위, 테스트만, 문서 업데이트

### 파일 생성 정책
기본: 기존 파일 수정 우선. 새 파일은 정당화 필요.
허용: tests/test_{service}.py, alembic/versions/, frontend-next/src/components/{feature}/
금지 (명시적 요청 없이): 유틸/헬퍼 파일, 새 디렉토리, 설정 파일

### 도구 선택 결정 트리
기능 개발? → /dev | 버그? → /fix | 리뷰? → /review | 테스트 실패? → /test-and-fix

파일 찾기? → Glob | 내용 검색? → Grep | 파일 읽기? → Read
브라우저 테스트? → Playwright MCP | 외부 라이브러리 문서? → context7 plugin

1-3 파일 단일 도메인 → 직접 수행 | 4+ 파일 단일 도메인 → 도메인 에이전트 위임 | 복수 도메인 → /dev

---

## Environment Variables (Required)

```bash
DATABASE_URL=postgresql+asyncpg://user:pass@host/db
DATABASE_URL_SYNC=postgresql://user:pass@host/db  # For Alembic
SECRET_KEY=your-secret-key-change-in-production
```

---

## Session Documentation

세션 80% 소모 시 `docs/summary_YYYYMMDD.md` 생성 (구현 내용, 이슈, 스키마 변경, 다음 TODO)

---

*Last updated: 2026-03-15*
