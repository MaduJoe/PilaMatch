# Claude Code Rules for PilaMatch

## Project Overview
PilaMatch - 필라테스/요가 강사 매칭 플랫폼

## Core Values
- **신뢰 (Trust)**: 안전한 거래 환경 제공이 최우선
- **Simple**: 복잡한 기능보다 핵심 기능에 집중
- **Stable**: 안정성 > 새로운 기능

---

## Development Rules

### 1. Session Documentation (필수)
> **세션의 80% 소모 시, 자동으로 docs/ 폴더에 세션 요약 문서 생성**

```
docs/summary_YYYYMMDD.md
```

문서 포함 내용:
- 구현된 기능 목록
- 해결한 이슈/버그
- 데이터베이스 스키마 변경사항
- 다음 단계 TODO
- 실행 방법

### 2. Code Standards
- **Backend**: FastAPI + SQLAlchemy async
- **Frontend**: Streamlit (MVP), React Native (future)
- **Database**: PostgreSQL (prod), SQLite (test)
- **Package Manager**: uv

### 3. Database Compatibility
- UUID는 `GUID` 커스텀 타입 사용 (CHAR(36))
- Enum은 `String(20)` 사용 (SQLEnum 금지)
- ARRAY는 `JSON` 타입으로 대체

### 4. Git Commit Convention
```
feat: 새로운 기능
fix: 버그 수정
docs: 문서 변경
refactor: 코드 리팩토링
test: 테스트 추가/수정
```

### 5. API Design
- REST 원칙 준수
- 에러 응답: `{"detail": {"code": "ERROR_CODE", "message": "..."}}`
- 인증: Bearer Token (JWT)

---

## Project Structure
```
PilaMatch/
├── backend/           # FastAPI 백엔드
├── frontend/          # Streamlit 프론트엔드
├── docs/              # 세션 요약 문서
├── CLAUDE.md          # Claude Code 규칙 (이 파일)
├── CLAUDE_RUNBOOK.md  # 구현 가이드
└── docker-compose.yml
```

---

## Quick Commands

```bash
# 개발 서버 실행
docker-compose up -d --build

# 로그 확인
docker-compose logs -f backend

# DB 초기화 (데이터 삭제)
docker-compose down -v && docker-compose up -d

# 테스트 실행
cd backend && uv run pytest

# API 문서
http://localhost:8000/api/v1/docs
```

---

## Trust Features Priority
1. 본인/사업자 인증 ✅
2. 보증금 시스템 ✅
3. 에스크로 결제 ✅
4. 노쇼 패널티 ✅

---

*Last updated: 2026-02-10*
