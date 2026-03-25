# PilaMatch

**수업 펑크를 10분 안에 막는 운영 시스템 -- 필라테스/요가 강사 & 센터**

> 센터가 긴급 호출 → 대기 강사 풀에서 자동 디스패치 → 선착순 수락 → GPS 체크인 → 양측 완료 확인. 119처럼, 확실하게.

---

## Problem & Solution

### 현재 시장의 문제

아침 9시, 강사가 결근 통보를 한다. 센터장은 카카오톡 단톡방에 "오늘 오전 대타 가능하신 분?"을 보낸다.
30분이 지나도 답이 없다. 수업이 펑크 난다.

| 기존 방식 | 문제점 |
|-----------|--------|
| **카톡 단톡방** | 메시지 묻힘, 검증 불가, 이력 없음 |
| **호호요가** | 앱 불안정, 노쇼 제재 없음, 지역 매칭 불가 |
| **지인 네트워크** | 범위 한정, 확장 불가 |

### PilaMatch의 답

네 가지 축으로 구조적 차별점을 만든다.

| 축 | 설명 | 구현 |
|----|------|------|
| **Trust-Tech** | 실명인증 기반 신뢰 — 행동 이력이 곧 등급 | SMS 본인인증, 사업자인증, Tier 등급제 (T1/T2/T3, C1/C2), 노쇼 3-strike 정지 |
| **Hyper-Local** | 거리 기반 매칭 — GPS Haversine 계산 | 5단계 거리 점수 (2km 이내 100점, 30km+ 10점), 이동 시간 추정 |
| **Seamless Handoff** | 인수인계 노트 — 강사가 바뀌어도 자연스러운 맞춤 수업 | 재사용 템플릿, Completeness Score, 민감정보 태그화 (개인정보보호법 준수) |
| **Auto Dispatch** | 119식 자동 호출 — Standby Pool + 3단계 반경 확장 | 긴급 호출 → 자동 매칭 → 선착순 수락 → GPS 체크인 → 양측 완료 확인 |

---

## 핵심 플로우

```
센터: 긴급 호출 버튼 (30초)
  |  카테고리, 시간, 시급 + 인수인계 노트
  v
시스템: Standby Pool에서 자동 디스패치
  |  1차: 5km 반경 → 2차: 10km → 3차: 15km
  |  Reliability Score 기반 후보 선별
  v
강사: 푸시 알림 수신 → 원탭 수락 (선착순)
  |  수락 즉시 인수인계 노트 전체 공개
  v
강사: GPS 체크인 (센터 200m 이내)
  |  출근 시간 자동 기록
  v
수업 완료 → 양측 완료 확인
  v
센터 지급 표시 → 강사 수령 확인
  v
상호 리뷰 → Tier 등급에 반영
```

```mermaid
flowchart LR
    A[긴급 호출] --> B[자동 디스패치]
    B --> C[선착순 수락]
    C --> D[인수인계 + 연락처 공개]
    D --> E[GPS 체크인]
    E --> F[수업 완료 확인]
    F --> G[지급 확인]
    G --> H[리뷰 → Tier 갱신]
```

---

## 3대 핵심 기능

### 1. Auto Dispatch Engine (자동 디스패치)

119 긴급 출동 시스템처럼, 센터가 호출하면 시스템이 최적의 강사를 자동으로 찾아 매칭한다.

| 기능 | 설명 |
|------|------|
| **Standby Pool** | 강사가 "오늘 대기 가능" ON — GPS 좌표 + 카테고리 + 최대 거리 설정 |
| **3단계 Cascading** | Wave 1: 5km 반경, 상위 5명 / Wave 2: 10km, 상위 10명 / Wave 3: 15km, 상위 15명 |
| **선착순 수락 (FCFS)** | 첫 수락 강사 자동 확정, 나머지 디스패치 자동 취소 |
| **Reliability Score** | 완료 이력, 노쇼/지각/취소 기록 기반 후보 선별 및 정렬 |
| **Self-Healing** | Wave별 3분 타임아웃, 미응답 시 자동 다음 Wave 발송 |
| **Fallback** | 3차 Wave 소진 시 수동 모드(manual)로 전환 |

### 2. 인수인계 노트 (Handoff Note)

"선생님이 바뀌어도 매끄러운 수업"의 핵심. 센터가 수업 맥락을 대타 강사에게 전달한다.

| 필드 | 공개 시점 | 예시 |
|------|----------|------|
| 수업 주제 | 공고 열람 시 | "허리 재활 시퀀스 3주차" |
| 진도 설명 | 공고 열람 시 | "지난주 브릿지까지 완료, 이번 주 사이드 킥" |
| 수업 분위기 | 공고 열람 시 | "차분한" / "에너지틱" |
| 기타 메모 | 공고 열람 시 | 자유 텍스트 |
| **회원 주의사항** | **수락 후** | "3번 회원 허리 디스크, 과신전 주의" |
| **기구 세팅** | **수락 후** | "리포머 스프링 빨2+초1, 발바는 1구" |

| 추가 기능 | 설명 |
|-----------|------|
| **재사용 템플릿** | 반복 수업용 인수인계 원클릭 재사용 (센터당 최대 20개) |
| **Completeness Score** | 인수인계 충실도 점수 — 필드 작성 비율 자동 계산 |
| **민감정보 태그화** | `member_caution_tags` 배열로 개인정보보호법 준수 구조화 |
| **강사 피드백** | 수업 완료 후 강사가 인수인계 노트에 피드백 작성 |

### 3. Trust Verification (신뢰 검증)

"확실하게 왔고, 확실하게 했다"를 시스템으로 증명한다.

| 기능 | 설명 |
|------|------|
| **GPS 체크인** | 센터 200m 이내 위치 인증 (Haversine 거리 계산) |
| **양측 완료 확인** | 센터 + 강사 독립 확인 → 양측 모두 확인 시 완료 처리 |
| **출동 성공률** | Dispatch Success Rate 추적 (총 디스패치 대비 완료 비율) |
| **Reliability Stats** | 총 디스패치, 총 완료, 총 체크인, 평균 체크인 거리 공개 |

---

## Trust-Tech: Tier 등급제

PilaMatch는 "점수"가 아니라 "행동 조건"으로 등급을 판정한다.

### 강사 등급 (Teacher Tier)

| 등급 | 라벨 | 조건 | 일일 지원 | 매칭 부스트 |
|------|------|------|----------|------------|
| **T1** | Basic | 본인인증 + 프로필 기본정보 | 3건 | 1.0x |
| **T2** | Verified | T1 + 신분증 인증 + 자격증 1개+ + 최근 30일 완료 2건+ + 노쇼 0 | 20건 | 1.0x |
| **T3** | Premium | T2 + 최근 30일 완료 5건+ + 노쇼 0 + 당일취소 0 + 지각 1회 이하 | 무제한 | 1.3x |

### 센터 등급 (Center Tier)

| 등급 | 라벨 | 조건 | 활성 공고 | 매칭 부스트 |
|------|------|------|----------|------------|
| **C1** | Basic | 본인인증 + 업체 기본정보 | 2건 | 1.0x |
| **C2** | Verified | C1 + 사업자인증 + 위치증빙 + 최근 30일 완료 2건+ + 확정후취소 1회 이하 | 10건 | 1.15x |

### 패널티 제재

| 패널티 | 제재 | 등급 영향 |
|--------|------|----------|
| **노쇼** | 14일 정지, 3회 누적 시 영구 정지 | T1 강등 |
| **당일 취소** | 7일 당일급구 제한 | T3 유지 불가 |
| **지각** | 기록 (월 2회 이상 시 T3 유지 불가) | Premium 조건 영향 |
| **확정 후 취소** (센터) | 기록 | C2 유지 불가 |

---

## Tech Stack

| Layer | 기술 | 비고 |
|-------|------|------|
| **Backend** | FastAPI 0.109+, Python 3.11+, async/await | uv 패키지 매니저 |
| **Database** | PostgreSQL 15 (prod) / SQLite (test) | SQLAlchemy 2.0 async ORM |
| **Cache** | Redis 7 | OTP 캐싱, in-memory fallback |
| **Frontend** | Next.js 15, React, TypeScript, Tailwind CSS | shadcn/ui, TanStack Query, Zod v4 |
| **Auth** | JWT (Access + Refresh), httpOnly Cookie | bcrypt, python-jose |
| **Distance** | Haversine formula | GPS 기반 실시간 거리 계산 |
| **Push** | FCM (Firebase Cloud Messaging) | 디스패치 알림, 수업 리마인더 |
| **Infra** | Docker Compose (4 services) | PostgreSQL, Redis, Backend, Frontend |

---

## Quick Start

```bash
# 1. Clone & configure
git clone https://github.com/your-repo/PilaMatch.git
cd PilaMatch
cp .env.example .env   # Edit .env (see Environment Variables below)

# 2. Start all services
docker-compose up -d --build

# 3. Access
#    API Docs:  http://localhost:8000/api/v1/docs
#    Frontend:  http://localhost:3000

# 4. View logs
docker-compose logs -f backend

# 5. Reset database (WARNING: deletes all data)
docker-compose down -v && docker-compose up -d
```

### Local Development

```bash
# Backend
cd backend
uv sync
alembic upgrade head
uv run uvicorn app.main:app --reload --port 8000

# Frontend (new terminal)
cd frontend-next
pnpm install && pnpm dev
```

---

## Active API Endpoints

### Auth
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/auth/signup` | 회원가입 |
| POST | `/auth/login` | 로그인 (JWT 발급) |
| POST | `/auth/refresh` | 토큰 갱신 |
| GET | `/auth/me` | 내 정보 조회 |
| POST | `/auth/logout` | 로그아웃 |
| POST | `/auth/password-reset/request` | 비밀번호 재설정 요청 |
| POST | `/auth/password-reset/confirm` | 비밀번호 재설정 확인 |

### Verification (본인/사업자 인증)
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/verification/phone/request` | SMS OTP 요청 |
| POST | `/verification/phone/verify` | OTP 검증 |
| POST | `/verification/business/verify` | 사업자등록번호 인증 |
| GET | `/verification/status` | 인증 상태 조회 |

### Profiles
| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/profiles/me` | 내 프로필 조회 |
| PUT | `/profiles/me` | 프로필 수정 (teaching_style 포함) |

### Tier (등급)
| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/tier/me` | 내 등급 조회 (뱃지, 다음 등급 요건 포함) |
| GET | `/tier/user/{user_id}` | 타인 등급 공개 조회 |
| GET | `/tier/requirements` | 전체 등급 체계 설명 |

### Penalties (패널티)
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/penalties/report` | 패널티 신고 (노쇼/당일취소/지각/확정후취소) |
| GET | `/penalties/me` | 내 패널티 이력 |

### Payment Confirmation (지급 확인)
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/applications/{id}/mark-paid` | 지급 완료 표시 (센터) |
| POST | `/payment-confirmations/{id}/confirm` | 수령 확인 (강사) |
| POST | `/payment-confirmations/{id}/dispute` | 미지급 신고 (강사) |
| GET | `/payment-confirmations/me` | 내 지급 이력 |

### Instructors
| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/instructors/{id}` | 강사 프로필 상세 (경력, 리뷰, 대타 이력, teaching_style) |

### Studios
| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/studios/{id}` | 스튜디오 프로필 상세 |

### Job Posts (대타 공고)
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/job-posts` | 공고 등록 (is_urgent=true 시 자동 디스패치 실행) |
| GET | `/job-posts` | 공고 목록 (필터링) |
| GET | `/job-posts/{id}` | 공고 상세 (has_handoff_note 포함) |
| GET | `/job-posts/for-me/with-matching` | 매칭 점수 포함 목록 (강사) |

### Handoff Notes (인수인계 노트)
| Method | Endpoint | 설명 |
|--------|----------|------|
| PUT | `/job-posts/{id}/handoff-note` | 인수인계 노트 생성/수정 (센터) |
| GET | `/job-posts/{id}/handoff-note` | 노트 조회 (역할+수락 여부에 따라 공개/전체 응답) |
| DELETE | `/job-posts/{id}/handoff-note` | 노트 삭제 (센터) |

### Applications (지원 + 수락)
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/job-posts/{id}/applications` | 지원서 제출 (강사) |
| GET | `/job-posts/{id}/applications` | 공고별 지원자 목록 (센터) |
| GET | `/applications/me` | 내 지원 목록 (강사) |
| POST | `/applications/{id}/withdraw` | 지원 철회 (강사) |
| **POST** | **`/applications/{id}/accept`** | **지원 수락 + 연락처 공개 (센터)** |

> `POST /applications/{id}/accept`는 수동 매칭(manual mode)의 핵심 엔드포인트이다.
> 자동 디스패치가 아닌 수동 모드에서 센터가 지원자를 직접 선택할 때 사용한다.
> 수락 즉시 양측 전화번호를 공개한다.
> ```json
> {
>     "application_id": "uuid",
>     "instructor_phone": "01012345678",
>     "instructor_name": "김필라",
>     "studio_phone": "0212345678",
>     "studio_name": "서초필라테스",
>     "studio_address": "서울시 서초구 ..."
> }
> ```

### Dispatch (자동 디스패치)

자동 디스패치는 `POST /job-posts` 에서 `is_urgent=true`로 공고를 생성하면 서버 내부에서 `DispatchEngine.start_auto_dispatch()`가 자동 실행된다. 별도의 trigger 엔드포인트는 없으며, 아래는 디스패치 진행 중 강사/센터가 사용하는 엔드포인트이다.

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/dispatch/{dispatch_record_id}/accept` | 디스패치 수락 — 선착순, 연락처 공개 (강사) |
| POST | `/dispatch/{dispatch_record_id}/decline` | 디스패치 거절 — 미응답 시 다음 Wave 트리거 (강사) |
| GET | `/dispatch/my-pending` | 내 대기 중 디스패치 목록 (강사) |
| GET | `/dispatch/job/{job_post_id}/status` | 디스패치 상태 조회 — Wave, 매칭 여부 (센터) |

### Availability (강사 대기 — Standby Pool)
| Method | Endpoint | 설명 |
|--------|----------|------|
| PUT | `/availability` | 대기 상태 ON/OFF + GPS 좌표 + 카테고리 설정 (강사) |
| GET | `/availability/me` | 내 대기 상태 조회 (강사) |

### Check-in (GPS 체크인)
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/jobs/{job_post_id}/checkin` | GPS 체크인 — 센터 200m 이내 위치 인증 (강사) |
| GET | `/jobs/{job_post_id}/checkin` | 체크인 기록 조회 |

### Completion (완료 확인)
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/jobs/{job_post_id}/complete` | 완료 확인 (센터 또는 강사, 양측 독립 확인) |
| GET | `/jobs/{job_post_id}/completion` | 완료 상태 조회 |
| GET | `/instructors/{user_id}/reliability` | 강사 신뢰도 통계 (출동 성공률, 체크인 횟수 등) |

### Handoff Templates (인수인계 템플릿)
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/studios/me/handoff-templates` | 템플릿 생성 (센터, 최대 20개) |
| GET | `/studios/me/handoff-templates` | 내 템플릿 목록 (센터) |
| PUT | `/studios/me/handoff-templates/{template_id}` | 템플릿 수정 |
| DELETE | `/studios/me/handoff-templates/{template_id}` | 템플릿 삭제 |
| POST | `/job-posts/{job_post_id}/handoff-note/from-template/{template_id}` | 템플릿을 인수인계 노트에 적용 |
| POST | `/job-posts/{job_post_id}/handoff-note/feedback` | 인수인계 노트 피드백 (강사, 수업 완료 후) |

### Backup Instructors (백업 강사)
| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/studios/me/backup-instructors` | 내 백업 강사 목록 |
| POST | `/studios/me/backup-instructors` | 백업 강사 추가 |
| PATCH | `/studios/me/backup-instructors/{instructor_id}` | 백업 강사 수정 |
| DELETE | `/studios/me/backup-instructors/{instructor_id}` | 백업 강사 삭제 |

### Reviews
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/contracts/{id}/reviews` | 리뷰 작성 (체크리스트 기반) |
| GET | `/reviews/{user_id}` | 사용자 리뷰 조회 |

### Reports (신고/차단)
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/reports` | 신고 접수 |
| POST | `/reports/block/{user_id}` | 사용자 차단 |

### Support (고객지원)
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/support/tickets` | 문의 접수 |
| GET | `/support/tickets/me` | 내 문의 목록 |

### Notifications (알림)
| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/notifications` | 알림 목록 |
| POST | `/notifications/{id}/read` | 알림 읽음 처리 |

---

## Matching Algorithm

최대 **6-factor** 매칭. GPS/스타일 데이터 유무에 따라 가중치가 동적으로 조정된다.
자동 디스패치 모드에서는 Reliability Score가 추가 가중 요소로 사용된다.

### 6-Factor (GPS + 스타일 available)

```mermaid
pie title 매칭 점수 가중치 (GPS + 스타일)
    "거리 (Haversine)" : 25
    "스타일 호환" : 20
    "경력 충족" : 20
    "자격증 보유" : 15
    "희망 시급" : 10
    "지역 일치" : 10
```

| Factor | Weight | 100점 기준 |
|--------|--------|-----------|
| **거리** | 25% | 2km 이내 |
| **스타일** | 20% | 전체 항목 일치 |
| **경력** | 20% | 요구 경력 충족 |
| **자격증** | 15% | 필요 자격증 전부 보유 |
| **시급** | 10% | 희망 범위 내 |
| **지역** | 10% | 활동 지역 일치 |

### 가중치 시나리오

| 시나리오 | 거리 | 스타일 | 경력 | 자격증 | 시급 | 지역 |
|----------|------|--------|------|--------|------|------|
| GPS + 스타일 | 25% | 20% | 20% | 15% | 10% | 10% |
| GPS만 | 35% | — | 25% | 15% | 15% | 10% |
| 스타일만 | — | 20% | 20% | 20% | 15% | 25% |
| 둘 다 없음 | — | — | 25% | 25% | 20% | 30% |

### 거리 점수 기준 (Haversine)

| 거리 | 점수 | 의미 |
|------|------|------|
| 0-2km | 100 | 도보/자전거 가능 |
| 2-5km | 80 | 10-15분 이동 |
| 5-10km | 60 | 대중교통 20분 |
| 10-20km | 40 | 30분 이동 |
| 20-30km | 20 | 장거리 |
| 30km+ | 10 | 현실적으로 어려움 |

### 스타일 점수 기준

일치하는 스타일 키의 비율 x 100. 데이터 없으면 중립 50점.

> T3 Premium 강사는 매칭 점수 1.3x 부스트, C2 Verified 센터 공고는 1.15x 부스트가 적용된다.

---

## Testing

총 **580개** 테스트 — Auto Dispatch, GPS 체크인, 완료 확인, 인수인계 템플릿, Tier 등급, 패널티, 지급 확인, 스타일 매칭, 백업 강사 등.

```bash
cd backend

# 전체 테스트
uv run pytest

# 커버리지 포함
uv run pytest --cov=app --cov-report=html

# 디스패치 엔진 테스트
uv run pytest tests/test_dispatch_engine.py -v

# GPS 체크인 테스트
uv run pytest tests/test_checkin.py -v

# 완료 확인 테스트
uv run pytest tests/test_completion.py -v

# 인수인계 템플릿 테스트
uv run pytest tests/test_handoff_template.py -v

# 인수인계 노트 테스트
uv run pytest tests/test_handoff_note.py -v

# 스타일 매칭 테스트
uv run pytest tests/test_style_matching.py -v

# 백업 강사 테스트
uv run pytest tests/test_backup_instructor.py -v

# Tier 등급 테스트
uv run pytest tests/test_tier_evaluation.py tests/test_tier_limits.py -v

# 패널티/지급 확인 테스트
uv run pytest tests/test_penalty_service.py tests/test_payment_confirmation.py -v

# 긴급 매칭 테스트
uv run pytest tests/test_urgent_matching.py -v
```

---

## Environment Variables

```bash
# === Database ===
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/pilamatch
DATABASE_URL_SYNC=postgresql://postgres:password@localhost:5432/pilamatch
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-password
POSTGRES_DB=pilamatch

# === Security ===
SECRET_KEY=your-super-secret-key-change-in-production  # Required, no default
DEBUG=false
APP_ENV=production

# === Redis ===
REDIS_URL=redis://redis:6379/0

# === SMS (Solapi) ===
SMS_PROVIDER=mock          # mock | solapi
SMS_API_KEY=your-api-key
SMS_API_SECRET=your-api-secret
SMS_SENDER_NUMBER=01012345678

# === 국세청 API (사업자 검증) ===
NTS_SERVICE_KEY=your-service-key

# === FCM (Push Notifications) ===
GOOGLE_APPLICATION_CREDENTIALS=/path/to/firebase-service-account.json

# === Frontend ===
NEXT_PUBLIC_API_URL=http://localhost:3000/api/v1
NEXT_PUBLIC_KAKAO_MAP_KEY=your-kakao-key
FRONTEND_URL=http://localhost:3000

# === PMF 후 재활성화 ===
# TOSS_CLIENT_KEY=...       # 프리미엄 구독 결제 (현재 비활성)
# TOSS_SECRET_KEY=...       # 프리미엄 구독 결제 (현재 비활성)
```

---

## PMF Metrics

PMF 검증을 위해 추적하는 핵심 지표.

| Metric | 정의 | 목표 |
|--------|------|------|
| **TTFA** (Time to First Accept) | 긴급 호출 → 첫 수락까지 소요 시간 | < 10분 |
| **Dispatch Success Rate** | 디스패치 시도 대비 수락 완료 비율 | > 80% |
| **GPS Check-in Rate** | 수락 건 대비 GPS 체크인 완료 비율 | > 90% |
| **Fill Rate** | 공고 대비 수락 완료 비율 | > 60% |
| **Repeat Rate** | 재사용률 (2주 내 재공고/재지원) | > 40% |
| **Tier Upgrade Rate** | T2+ 등급 달성 비율 | > 30% |
| **Handoff Note Rate** | 공고 중 인수인계 노트 첨부 비율 | > 50% |
| **Standby Pool Size** | 구별 평균 대기 강사 수 | > 5명/구 |

---

## Production Checklist

- [ ] `SECRET_KEY` 변경 (강력한 랜덤 문자열)
- [ ] `DEBUG=false`, `APP_ENV=production` 설정
- [ ] `SMS_PROVIDER=solapi` + API 키 설정
- [ ] FCM 서비스 계정 키 설정 (`GOOGLE_APPLICATION_CREDENTIALS`)
- [ ] CORS 설정 검토 (허용된 origin만)
- [ ] Rate Limiting 설정 확인 (slowapi)
- [ ] PostgreSQL 백업 전략 수립
- [ ] SSL/TLS 인증서 설정
- [ ] 모니터링 설정 (Sentry)

---

## UI/UX 디자인 (v5.0)

### 모바일 퍼스트 설계

PilaMatch는 긴급 대타 매칭 특성상 모바일 사용이 90%+ 예상되어, 모바일 퍼스트 UI로 설계되었다.

### 주요 UI 컴포넌트

| 컴포넌트 | 파일 | 설명 |
|----------|------|------|
| **Bottom Tab Bar** | `components/layout/bottom-tab-bar.tsx` | 하단 네비게이션 (탭 인디케이터 + 아이콘 하이라이트) |
| **Applicant Card** | `components/offers/applicant-card.tsx` | 지원자 카드 (Tier 뱃지, 연락처, 전화/문자 버튼) |
| **Job Creation Form** | `components/jobs/job-creation-form.tsx` | 공고 등록 폼 (7단계, 시급 범위, 핑크 긴급 버튼, 스타일 선택) |
| **Handoff Note Form** | `components/jobs/handoff-note-form.tsx` | 인수인계 노트 입력 (접이식, 긴급 대타 넛지, 민감 필드 자물쇠) |
| **Job Card** | `components/jobs/job-card.tsx` | 공고 카드 (매칭 점수, D-Day, 거리, 인수인계 배지) |
| **Job Detail Dialog** | `components/jobs/job-detail-dialog.tsx` | 공고 상세 (거리/스타일 점수 그리드) |
| **Teaching Style Selector** | `components/profile/teaching-style-selector.tsx` | 수업 스타일 토글 선택기 (4차원) |
| **Instructor App List** | `components/applications/instructor-application-list.tsx` | 강사 지원 현황 (매칭 완료 시 연락처 표시) |
| **Backup Instructor List** | `components/backup/backup-instructor-list.tsx` | 백업 강사 목록/관리 (CRUD, 우선순위 배지) |
| **Backup Suggest Prompt** | `components/backup/backup-suggest-prompt.tsx` | 수락 후 "백업 강사 등록" 프롬프트 |
| **Tier Badge** | `components/trust/tier-badge.tsx` | 등급 뱃지 (T1 Basic / T2 Verified / T3 Premium) |

### 핵심 UX 패턴

1. **긴급 호출 30초**: 센터가 긴급 호출 버튼을 누르면 카테고리 + 시간 + 시급 + 인수인계 템플릿 선택으로 30초 안에 등록 완료
2. **연락처 즉시 공개**: 수락 즉시 양측 전화번호가 표시되며, 전화/문자 버튼으로 원탭 연락 가능
3. **인수인계 노트 넛지**: 긴급 대타 선택 시 "인수인계 노트를 남기면 강사가 바뀌어도 자연스럽게 맞춤 수업이 이어집니다" 표시
4. **민감 정보 보호**: 회원 주의사항/기구 세팅은 자물쇠 아이콘 + "수락 후 공개" 라벨
5. **인수인계 배지**: 공고 카드에 "인수인계" 배지 → 준비된 센터라는 신뢰 시그널
6. **시급 범위 선택**: 최소/최대 시급을 버튼으로 선택, "구체적인 금액은 연락 후 조율" 안내
7. **긴급 공고**: 소프트 핑크 컬러로 긴급성 표현 (공격적 빨강 지양)
8. **공고 상태 시각화**: 좌측 컬러 바 (초록=모집중, 파랑=채용완료, 회색=마감)
9. **활성/지난 공고 분리**: 활성 공고 상단, 지난 공고 하단 (투명도 75%)
10. **백업 강사 제안**: 수락 후 "이 강사를 백업 목록에 추가하시겠습니까?" 프롬프트

---

## 테스트 계정 (개발용)

Docker Compose로 로컬 환경 구축 후, `/auth/signup`으로 계정을 생성하거나 아래 스크립트를 사용한다.

```bash
BASE="http://localhost:8000/api/v1/auth"

# 강사 계정
curl -X POST "$BASE/signup" -H "Content-Type: application/json" \
  -d '{"email":"gangsa1@test.com","password":"Test1234","role":"instructor","display_name":"김강사"}'

# 센터 계정
curl -X POST "$BASE/signup" -H "Content-Type: application/json" \
  -d '{"email":"studio1@test.com","password":"Test1234","role":"studio","business_name":"필라테스센터"}'
```

> **비밀번호 규칙**: 8자 이상, 대문자 1개 이상 포함 필수

프로필 완성 후 대기 상태 ON (`PUT /availability`) → 긴급 공고 생성 → 자동 디스패치 플로우를 테스트할 수 있다.

---

## 비활성화 기능 (PMF 후 재활성화)

아래 기능은 코드 기반에 완전히 구현되어 있으나, PMF 피벗 기간 동안 라우터에서 비활성화되었다.
`backend/app/api/v1/router.py`에서 주석 해제하면 즉시 사용 가능하다.

| 기능 | 라우터 | 상태 |
|------|--------|------|
| Trust Score API (점수제) | `/trust-score` | 비활성 (Tier 등급제로 대체) |
| 프리미엄 멤버십 (월 9,900원) | `/subscriptions` | 비활성 |
| Offer 플로우 | `/offers` | 비활성 (accept로 대체) |
| Contract 상태 머신 | `/contracts` | 비활성 |
| 실시간 채팅 (WebSocket) | `/threads` | 비활성 |
| 지원서 템플릿 (Premium) | `/templates` | 비활성 |

---

## License

Private - All rights reserved

---

*Last updated: 2026-03-25 (v5.0: Auto Dispatch Engine + Trust Verification + Handoff Templates)*
