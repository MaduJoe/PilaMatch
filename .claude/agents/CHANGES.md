# 에이전트 파일 보완 사항 및 이유

## 전체 공통 변경 (8개 파일 모두 해당)

### 1. `tools` 필드 추가 — 모든 파일에 누락되어 있었음

**문제**: `tools` 필드가 없으면 에이전트가 메인 세션의 **모든 도구를 상속**합니다.
이는 보안 위험이며, 불필요한 도구 접근으로 토큰 낭비와 의도치 않은 파일 수정이 발생할 수 있습니다.

**변경**:
| 에이전트 | 부여한 tools | 이유 |
|----------|-------------|------|
| backend-api | Read, Write, Edit, Bash, Grep, Glob, Task | 코드 작성 + 서버 실행/테스트 필요. Task 추가로 하위 작업 위임 가능 |
| database | Read, Write, Edit, Bash, Grep, Glob | 마이그레이션 생성/적용에 Bash 필요 |
| devops | Read, Write, Edit, Bash, Grep, Glob | 인프라 파일 수정 + docker 명령 실행 필요 |
| doc-writer | Read, Write, Edit, Grep, Glob | **Bash 제외** — 문서 작성에 셸 명령 불필요, 실수로 시스템 변경 방지 |
| frontend-ui | Read, Write, Edit, Bash, Grep, Glob | UI 코드 작성 + streamlit 실행 확인 필요 |
| payment-trust | Read, Write, Edit, Bash, Grep, Glob | 결제 코드 작성 + 테스트 실행 필요 |
| **security-reviewer** | **Read, Grep, Glob만** | **가장 중요한 변경.** 원본에 "읽기 전용" 규칙이 시스템 프롬프트에만 있고 tools로 강제하지 않아, 모든 도구를 상속받아 실제로는 코드를 수정할 수 있었음. Write/Edit/Bash를 제거하여 읽기 전용을 기술적으로 강제 |
| test-qa | Read, Write, Edit, Bash, Grep, Glob | 테스트 작성 + pytest 실행 필요 |

---

### 2. `description`에 `MUST BE USED` 키워드 추가

**문제**: 원본은 모두 `Use proactively when...` 으로만 끝남.
Claude Code 공식 문서와 커뮤니티 베스트 프랙티스에 따르면 `MUST BE USED`가 자동 위임 확률을 높입니다.

**변경**: 모든 파일의 description 앞에 `MUST BE USED for` 추가.

---

### 3. `description`에 **구체적 파일 경로** 추가

**문제**: 원본 description은 "백엔드 코드 작업 시"처럼 추상적.
Claude Code는 description과 현재 작업을 매칭하므로, 구체적 경로가 있어야 정확히 라우팅됩니다.

**변경 예시**:
- backend-api: `app/api/, app/services/, app/tasks/ 하위 파일 수정 시 자동 위임` 추가
- database: `app/models/ 하위 파일 수정, alembic/ 마이그레이션` 추가
- security-reviewer: `core/security.py, core/deps.py` 명시
- 각 에이전트마다 담당 디렉토리/파일 패턴 명시

---

### 4. `Context Discovery` 섹션 추가 — 모든 파일에 누락

**문제**: 서브에이전트는 **매번 새로운 컨텍스트 윈도우**에서 시작합니다.
메인 에이전트의 컨텍스트를 전혀 모르는 상태에서 작업을 시작하므로,
"먼저 무엇을 확인할지"를 명시하지 않으면 엉뚱한 코드를 작성하거나 기존 패턴을 무시합니다.

**변경**: 각 에이전트별로 `## Context Discovery (매 호출 시 먼저 수행)` 섹션 추가.
프로젝트 구조와 기존 패턴을 파악하는 3-4개의 구체적 명령어를 포함.

---

## 개별 파일 변경

### backend-api.md

| 항목 | 원본 | 변경 | 이유 |
|------|------|------|------|
| model | `opus` | `sonnet` | 일반적인 API 라우터/서비스 작성은 sonnet으로 충분. opus는 토큰 비용이 ~5배. 복잡한 아키텍처 결정이 아닌 한 sonnet이 비용 대비 성능 최적 |
| tools | (없음) | `Read, Write, Edit, Bash, Grep, Glob, Task` | Task 도구 추가 — 복잡한 백엔드 작업에서 하위 탐색 위임 가능 |

### database.md

| 항목 | 원본 | 변경 | 이유 |
|------|------|------|------|
| model | `opus` | `sonnet` | 스키마 정의, 마이그레이션 생성은 패턴이 정형화되어 있어 sonnet 충분. 쿼리 최적화도 sonnet이 잘 처리함 |

### devops.md

| 항목 | 원본 | 변경 | 이유 |
|------|------|------|------|
| model | `opus` | `sonnet` | Dockerfile, docker-compose, CI/CD yaml 작성은 정형화된 작업. sonnet으로 충분 |
| color | (없음) | `gray` | 원본에만 color 필드 누락. UI에서 어떤 에이전트가 실행 중인지 식별하는 데 사용 |

### doc-writer.md

| 항목 | 원본 | 변경 | 이유 |
|------|------|------|------|
| model | `opus` | `haiku` | **문서 작성은 가장 가벼운 작업.** 마크다운 문서, CHANGELOG 업데이트 등은 haiku로 충분하며, 비용 절감 효과가 큼 (opus 대비 ~15배 저렴). 문서 품질은 시스템 프롬프트의 규칙으로 보장 |
| tools | (없음) | `Read, Write, Edit, Grep, Glob` | **Bash 의도적 제외** — 문서 작성에 셸 명령 실행이 불필요. 실수로 시스템 변경하는 것을 방지 |

### frontend-ui.md

| 항목 | 원본 | 변경 | 이유 |
|------|------|------|------|
| description | 경로 정보 없음 | `frontend/ 하위 파일 수정 시 자동 위임` 추가 | backend-api와의 라우팅 혼동 방지. 명확한 디렉토리 바운더리 설정 |

(model: sonnet 유지 — 원본이 이미 적절)

### payment-trust.md

| 항목 | 원본 | 변경 | 이유 |
|------|------|------|------|
| model | `opus` | `opus` (유지) | **결제/금융 로직은 opus 유지가 정당.** 금액 계산 정확성, 엣지 케이스 처리, 멱등성 보장 등 실수 비용이 매우 높은 도메인. 비용보다 정확성이 우선 |
| description | 서비스 파일 미명시 | 구체적 파일 7개 명시 | `services/escrow.py, services/deposit.py, services/penalty.py` 등을 명시하여 정확한 라우팅 보장 |

### security-reviewer.md

| 항목 | 원본 | 변경 | 이유 |
|------|------|------|------|
| tools | **(없음 — 치명적)** | **`Read, Grep, Glob`만** | **가장 중요한 수정.** 원본은 시스템 프롬프트에 "읽기 전용"이라고만 적혀 있고 tools 제한이 없어, 실제로는 Write/Edit/Bash 모두 사용 가능했음. 보안 감사관이 코드를 수정할 수 있다면 감사의 의미가 없음 |

### test-qa.md

변경 사항: 공통 변경(tools, MUST BE USED, Context Discovery)만 적용.
원본이 이미 잘 작성되어 있었음 (model: sonnet, color: purple 등).

---

## 모델 비용 최적화 요약

| 에이전트 | 원본 | 변경 | 절감 근거 |
|----------|------|------|----------|
| backend-api | opus | **sonnet** | 정형화된 API 작업, sonnet 충분 |
| database | opus | **sonnet** | 스키마/마이그레이션 패턴화 작업 |
| devops | opus | **sonnet** | 인프라 설정 파일 작업 |
| doc-writer | opus | **haiku** | 마크다운 문서 작성, 가장 가벼운 작업 |
| frontend-ui | sonnet | sonnet | 유지 |
| payment-trust | opus | **opus** | 금융 정확성 필수, 유지 |
| security-reviewer | sonnet | sonnet | 유지 |
| test-qa | sonnet | sonnet | 유지 |

**결과**: 8개 중 4개 에이전트의 모델을 다운그레이드하여 비용 절감.
opus가 정당한 곳(payment-trust)만 유지.
