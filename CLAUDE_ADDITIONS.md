
---

## Testing Workflow

### 테스트 피드백 루프 (필수)

> **Claude에게 작업을 검증할 방법을 제공하는 것이 최종 결과물 품질을 2~3배 높이는 가장 중요한 요소다.**

모든 기능 구현은 다음 루프를 따른다:

```
구현 → 테스트 작성 → 실행 → 실패 시 수정 → 재실행 → 통과 시 커밋
```

### 테스트 실행 규칙

| 변경 대상 | 필수 테스트 | 명령어 |
|-----------|------------|--------|
| `app/services/` | 단위 테스트 | `uv run pytest tests/test_{service}.py -v` |
| `app/api/` | API 통합 테스트 | `uv run pytest tests/test_{endpoint}.py -v` |
| `app/models/` | 스키마 + 기존 테스트 전체 | `uv run pytest --cov=app` |
| `services/escrow.py`, `penalty.py`, `deposit.py` | 결제/신뢰 테스트 (필수) | `uv run pytest tests/test_payment*.py tests/test_penalty*.py -v` |
| `core/security.py`, `core/deps.py` | 보안 테스트 | `uv run pytest tests/test_auth.py -v` |
| `frontend/` | 수동 브라우저 검증 또는 Playwright | 아래 E2E 섹션 참조 |

### 테스트 작성 기준

- **커버리지 목표**: 핵심 서비스 80% 이상, 전체 60% 이상
- **필수 케이스**: 정상(Happy path) + 엣지케이스 + 에러 케이스 최소 3개
- **결제/신뢰 관련**: 금액 불일치, 중복 요청, 타임아웃, 상태 전이 오류 반드시 포함
- **Mock 대상**: SMS API, 토스페이먼츠 API, 국세청 API → 외부 서비스는 항상 Mock
- **테스트 통과 전 커밋 금지**: 실패하는 테스트가 있으면 수정 후 재실행

### 테스트 우선순위 (P0 → P2)

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

### E2E 테스트 (Playwright)

결제, 인증 등 크리티컬 플로우에 대해 Playwright 브라우저 테스트를 사용한다.

```bash
# Playwright 설치 (최초 1회)
pip install playwright
playwright install chromium

# E2E 테스트 실행
uv run pytest tests/e2e/ -v
```

**E2E 테스트 대상 (크리티컬 플로우만)**:
1. 회원가입 → 인증 → 보증금 입금 → 서비스 이용 가능
2. 공고 작성 → 매칭 → 지원 → 오퍼 → 계약 → 결제 → 완료
3. 노쇼 신고 → 패널티 → 보증금 차감 → 3회 시 계정 정지
4. 프리미엄 구독 → 혜택 적용 확인

### 테스트 실패 시 행동 규칙

```
1. 에러 메시지 읽고 원인 분석
2. 테스트가 잘못된 경우 → 테스트 수정
3. 코드가 잘못된 경우 → 코드 수정
4. 수정 후 반드시 재실행 (최대 3회 반복)
5. 3회 반복 후에도 실패 → 원인과 시도한 방법을 정리하여 사용자에게 보고
```

---

## Slash Commands

### 테스트 관련 커맨드

아래 파일들을 `.claude/commands/` 디렉토리에 생성한다.

#### `/test-and-fix` — 테스트 실행 & 자동 수정

```markdown
<!-- .claude/commands/test-and-fix.md -->
다음 단계를 순서대로 수행해:

1. **테스트 실행**:
   ```bash
   cd backend && uv run pytest tests/ -v --tb=short 2>&1 | head -100
   ```

2. **결과 분석**:
   - 모두 통과 → "✅ 전체 테스트 통과" 출력 후 종료
   - 실패 있음 → 실패한 테스트 목록 정리

3. **실패 수정** (최대 3회 반복):
   - 각 실패 원인 분석
   - 코드 또는 테스트 수정
   - 재실행하여 확인

4. **최종 보고**:
   - 통과/실패 테스트 수
   - 수정한 파일 목록
   - 남은 이슈 (있다면)
```

#### `/test-coverage` — 커버리지 리포트

```markdown
<!-- .claude/commands/test-coverage.md -->
커버리지 분석을 수행해:

1. 실행:
   ```bash
   cd backend && uv run pytest --cov=app --cov-report=term-missing -q 2>&1 | tail -40
   ```

2. 커버리지 80% 미만인 파일 식별

3. 가장 중요한 미커버 파일 TOP 3에 대해:
   - 누락된 테스트 케이스 제안
   - 우선순위 표시 (P0/P1/P2)

4. 전체 커버리지 요약 테이블 출력
```

#### `/test-payment` — 결제/신뢰 시스템 집중 테스트

```markdown
<!-- .claude/commands/test-payment.md -->
결제 및 신뢰 시스템 전체를 집중 테스트해:

1. **관련 테스트 실행**:
   ```bash
   cd backend && uv run pytest tests/test_escrow*.py tests/test_penalty*.py tests/test_deposit*.py tests/test_contract*.py -v 2>&1
   ```

2. **커버리지 확인**:
   ```bash
   cd backend && uv run pytest --cov=app/services/escrow --cov=app/services/penalty --cov=app/services/deposit --cov=app/services/contract --cov-report=term-missing -q 2>&1
   ```

3. **누락 시나리오 확인**:
   - 에스크로: 생성 → 홀드 → 릴리즈 → 정산 전체 플로우
   - 패널티: 노쇼 신고 → 차감 → 누적 → 3회 정지
   - 보증금: 입금 → 잔액 확인 → 차감 → 잔액 부족 시 에러
   - 계약 상태 전이: 모든 valid/invalid 전이 테스트

4. **누락된 테스트가 있으면 작성 후 실행**
```

#### `/verify-app` — 앱 전체 동작 검증

```markdown
<!-- .claude/commands/verify-app.md -->
앱이 정상 동작하는지 전체 검증해:

1. **서비스 상태 확인**:
   ```bash
   docker-compose ps
   curl -s http://localhost:8000/api/v1/docs | head -5
   curl -s http://localhost:8501 | head -5
   ```

2. **핵심 API 헬스체크**:
   ```bash
   # 인증
   curl -s -X POST http://localhost:8000/api/v1/auth/register \
     -H "Content-Type: application/json" \
     -d '{"email":"test@test.com","password":"Test1234!","role":"instructor"}'
   
   # 공고 목록
   curl -s http://localhost:8000/api/v1/jobs | head -20
   ```

3. **DB 상태 확인**:
   ```bash
   docker-compose exec db psql -U postgres -d studiobridge -c "SELECT COUNT(*) FROM users;"
   ```

4. **결과 리포트**:
   - ✅/❌ 각 서비스 상태
   - 발견된 문제 severity별 정리 (Critical/Warning/Info)
   - 수정 제안
```

#### `/commit-push-pr` — 커밋 & PR 생성

```markdown
<!-- .claude/commands/commit-push-pr.md -->
변경사항을 커밋하고 PR을 생성해:

1. **변경 파일 확인**: `git status && git diff --stat`

2. **테스트 실행** (변경된 파일 관련):
   ```bash
   cd backend && uv run pytest tests/ -v --tb=short -q 2>&1 | tail -10
   ```

3. **테스트 통과 시에만 진행**:
   - 변경 내용 분석하여 conventional commit 메시지 생성
   - `git add -A && git commit -m "{message}"`
   - `git push origin HEAD`
   - PR 생성 (가능하면 gh CLI 사용)

4. **테스트 실패 시**: 커밋 중단, 실패 내용 보고
```

---

## Verification Subagents

### verify-app 에이전트 (앱 검증 전문)

```markdown
<!-- .claude/agents/verify-app.md -->
---
name: verify-app
description: StudioBridge 앱 전체 동작 검증 전문 에이전트
---

너는 StudioBridge QA 엔지니어다.

## 검증 항목

### 1. 인프라 검증
- Docker 컨테이너 상태 (backend, frontend, db)
- 포트 접근 가능성 (8000, 8501, 5432)

### 2. API 검증
- 인증: 회원가입 → 로그인 → 토큰 발급 → 인증된 요청
- 핵심 CRUD: 공고 생성/조회, 지원 생성/조회, 계약 생성
- 결제: 에스크로 생성, 웹훅 처리
- 에러 처리: 잘못된 입력, 미인증 요청, 권한 없는 접근

### 3. 상태 전이 검증
- 계약: CONFIRMED → IN_PROGRESS → COMPLETED (정상)
- 계약: CONFIRMED → CANCELLED (취소)
- 잘못된 전이 시도 → 에러 반환 확인

### 4. 비즈니스 로직 검증
- 보증금 미입금 시 서비스 이용 차단
- 노쇼 패널티 누적 확인
- 프리미엄 혜택 적용 확인
- 매칭 점수 계산 정확성

## 결과 출력
검증 결과를 다음 형식으로 정리:

| 항목 | 상태 | 비고 |
|------|------|------|
| ... | ✅/❌ | ... |

Critical 이슈는 즉시 보고, Warning은 목록화.
```

### test-qa 에이전트 강화 (기존 에이전트 업데이트)

```markdown
<!-- .claude/agents/test-qa.md 에 아래 내용 추가/업데이트 -->
---
name: test-qa
description: 테스트 작성, 실행, 커버리지 분석 전문 에이전트
---

너는 StudioBridge 테스트 엔지니어다.

## 역할
- 단위 테스트, 통합 테스트, E2E 테스트 작성
- 테스트 실행 및 실패 원인 분석
- 커버리지 분석 및 누락 케이스 식별

## 테스트 작성 규칙

### 파일 네이밍
- `tests/test_{대상 서비스명}.py`
- E2E: `tests/e2e/test_{플로우명}.py`

### 구조
```python
import pytest
from httpx import AsyncClient

class TestFeatureName:
    """기능명 테스트"""
    
    async def test_happy_path(self, client: AsyncClient):
        """정상 케이스"""
        ...
    
    async def test_edge_case(self, client: AsyncClient):
        """엣지 케이스 - {설명}"""
        ...
    
    async def test_error_case(self, client: AsyncClient):
        """에러 케이스 - {설명}"""
        ...
```

### Mock 패턴
```python
# 토스페이먼츠 Mock
@pytest.fixture
def mock_toss_payment(mocker):
    return mocker.patch(
        "app.services.escrow.TossPaymentClient.confirm",
        return_value={"status": "DONE", "paymentKey": "test_pk"}
    )

# SMS Mock
@pytest.fixture
def mock_sms(mocker):
    return mocker.patch(
        "app.services.verification.send_sms",
        return_value=True
    )
```

### 결제/신뢰 테스트 필수 시나리오
1. 에스크로 생성 → 금액 검증 → 홀드 → 완료 시 릴리즈
2. 에스크로 취소 → 환불 처리
3. 노쇼 신고 → 패널티 30k 차감 → 보증금에서 차감
4. 패널티 3회 → 계정 정지 → 서비스 이용 불가 확인
5. 보증금 잔액 부족 → 에러 반환
6. 중복 웹훅 → 멱등성 확인

## 실행 후 행동
- 전체 통과 → 커버리지 리포트 출력
- 실패 있음 → 원인 분석 → 수정 가능하면 수정 → 재실행 (최대 3회)
- 수정 불가 → 이슈 정리하여 보고
```


## ============================================================
## 추가로, 기존 "Agent Delegation Rules" 테이블에 verify-app 행 추가:
## ============================================================

# | **verify-app** | 앱 전체 동작 검증, 배포 전 체크, 서비스 헬스체크, 통합 검증 |


## ============================================================
## 추가로, 기존 "Development Rules > 4. Testing Requirements" 를 아래로 교체:
## ============================================================

# ### 4. Testing Requirements
# - 모든 기능 구현 후 반드시 관련 테스트 작성 및 통과 확인
# - 결제/신뢰 관련 변경 시 `/test-payment` 필수 실행
# - PR 생성 전 `/test-and-fix` 필수 실행
# - 커버리지 60% 미만 시 테스트 추가 후 커밋
# - Mock 대상: SMS API, 토스페이먼츠 API, 국세청 API
# - E2E 테스트: 결제 플로우, 인증 플로우에 대해 Playwright 사용