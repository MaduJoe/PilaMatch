# PilaMatch

**긴급 대타 매칭 플랫폼 -- 필라테스/요가 강사 & 스튜디오**

> "실명으로 검증된 강사가, 20분 거리에서, 30분 만에 대타를 확정한다."

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

세 가지 축으로 구조적 차별점을 만든다.

| 축 | 설명 | 구현 |
|----|------|------|
| **Trust-Tech** | 실명인증 기반 신뢰 -- 행동 이력이 곧 등급 | SMS 본인인증, 사업자인증, Tier 등급제 (T1/T2/T3, C1/C2), 노쇼 3-strike 정지 |
| **Hyper-Local** | 거리 기반 매칭 -- GPS Haversine 계산 | 5단계 거리 점수 (2km 이내 100점, 30km+ 10점), 이동 시간 추정 |
| **Urgent Matching** | 긴급 대타 특화 -- 공고 작성 3분, 지원 원탭 | 수락 즉시 연락처 공개, 직접 전화/카톡으로 확정 |

---

## 핵심 플로우

```
센터: 대타 공고 작성 (3분)
  |  카테고리, 날짜/시간, 시급, 위치(GPS)
  v
강사: 공고 확인 + 매칭 점수 확인
  |  거리, 경력, 자격증, 시급 -- 한눈에 판단
  v
강사: 원탭 지원
  |  커버레터 (선택)
  v
센터: 지원자 프로필 확인
  |  이력, 리뷰, 거리, Tier 등급, 노쇼 이력
  v
센터: 수락 (POST /applications/{id}/accept)
  |  즉시 양측 연락처 공개
  v
직접 전화/카톡으로 최종 확정
  v
수업 완료 → 센터 지급 표시 → 강사 수령 확인
  v
상호 리뷰 → Tier 등급에 반영
```

```mermaid
flowchart LR
    A[대타 공고 작성] --> B[강사 매칭 + 지원]
    B --> C[센터 수락]
    C --> D[연락처 공개]
    D --> E[직접 연락 → 수업]
    E --> F[지급 확인]
    F --> G[상호 리뷰 → Tier 갱신]
```

---

## Trust-Tech: Tier 등급제

PilaMatch는 "점수"가 아니라 "행동 조건"으로 등급을 판정한다.

### 강사 등급 (Teacher Tier)

| 등급 | 라벨 | 조건 | 일일 지원 | 매칭 부스트 |
|------|------|------|----------|------------|
| **T1** | Basic | 본인인증 + 프로필 기본정보 | 3건 | 1.0x |
| **T2** | Verified | T1 + 신분증 인증 + 자격증 1개+ + 최근 30일 완료 2건+ + 노쇼 0 | 20건 | 1.0x |
| **T3** | Pro | T2 + 최근 30일 완료 5건+ + 노쇼 0 + 당일취소 0 + 지각 1회 이하 | 무제한 | 1.3x |

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
| **지각** | 기록 (월 2회 이상 시 T3 유지 불가) | Pro 조건 영향 |
| **확정 후 취소** (센터) | 기록 | C2 유지 불가 |

---

## Tech Stack

| Layer | 기술 | 비고 |
|-------|------|------|
| **Backend** | FastAPI 0.109+, Python 3.11+, async/await | uv 패키지 매니저 |
| **Database** | PostgreSQL 15 (prod) / SQLite (test) | SQLAlchemy 2.0 async ORM |
| **Cache** | Redis 7 | OTP 캐싱, in-memory fallback |
| **Frontend** | Next.js 15, React, TypeScript, Tailwind CSS | shadcn/ui, Zustand |
| **Auth** | JWT (Access + Refresh), httpOnly Cookie | bcrypt, python-jose |
| **Distance** | Haversine formula | GPS 기반 실시간 거리 계산 |
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
| PUT | `/profiles/me` | 프로필 수정 |

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
| GET | `/instructors/{id}` | 강사 프로필 상세 (경력, 리뷰, 대타 이력) |

### Studios
| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/studios/{id}` | 스튜디오 프로필 상세 |

### Job Posts (대타 공고)
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/job-posts` | 공고 등록 (스튜디오) |
| GET | `/job-posts` | 공고 목록 (필터링) |
| GET | `/job-posts/{id}` | 공고 상세 |
| GET | `/job-posts/for-me/with-matching` | 매칭 점수 포함 목록 (강사) |

### Applications (지원 + 수락)
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/job-posts/{id}/applications` | 지원서 제출 (강사) |
| GET | `/job-posts/{id}/applications` | 공고별 지원자 목록 (스튜디오) |
| GET | `/applications/me` | 내 지원 목록 (강사) |
| POST | `/applications/{id}/withdraw` | 지원 철회 (강사) |
| **POST** | **`/applications/{id}/accept`** | **지원 수락 + 연락처 공개 (스튜디오)** |

> `POST /applications/{id}/accept`는 PMF 피벗의 핵심 엔드포인트이다.
> 기존 Offer → Contract 플로우를 대체하여, 수락 즉시 양측 전화번호를 공개한다.
> 응답 예시:
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

GPS 좌표가 있으면 **5-factor** (거리 가중), 없으면 **4-factor** (지역 기반).

### 5-Factor (GPS available)

```mermaid
pie title 매칭 점수 가중치 (GPS 활성)
    "거리 (Haversine)" : 35
    "경력 충족" : 25
    "자격증 보유" : 15
    "희망 시급" : 15
    "지역 일치" : 10
```

| Factor | Weight | 100점 기준 |
|--------|--------|-----------|
| **거리** | 35% | 2km 이내 |
| **경력** | 25% | 요구 경력 충족 |
| **자격증** | 15% | 필요 자격증 전부 보유 |
| **시급** | 15% | 희망 범위 내 |
| **지역** | 10% | 활동 지역 일치 |

### 거리 점수 기준 (Haversine)

| 거리 | 점수 | 의미 |
|------|------|------|
| 0-2km | 100 | 도보/자전거 가능 |
| 2-5km | 80 | 10-15분 이동 |
| 5-10km | 60 | 대중교통 20분 |
| 10-20km | 40 | 30분 이동 |
| 20-30km | 20 | 장거리 |
| 30km+ | 10 | 현실적으로 어려움 |

### 4-Factor (GPS 없음, fallback)

지역 30% / 경력 25% / 자격증 25% / 시급 20%

> T3 Pro 강사는 매칭 점수 1.3x 부스트, C2 Verified 센터 공고는 1.15x 부스트가 적용된다.

---

## Testing

총 **327개** 테스트 -- Tier 등급, 패널티, 지급 확인, 긴급 매칭, 이벤트 로그 등.

```bash
cd backend

# 전체 테스트
uv run pytest

# 커버리지 포함
uv run pytest --cov=app --cov-report=html

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
| **TTFA** (Time to First Accept) | 공고 작성 → 첫 수락까지 소요 시간 | < 30분 |
| **Fill Rate** | 공고 대비 수락 완료 비율 | > 60% |
| **Repeat Rate** | 재사용률 (2주 내 재공고/재지원) | > 40% |
| **Tier Upgrade Rate** | T2+ 등급 달성 비율 | > 30% |

---

## Production Checklist

- [ ] `SECRET_KEY` 변경 (강력한 랜덤 문자열)
- [ ] `DEBUG=false`, `APP_ENV=production` 설정
- [ ] `SMS_PROVIDER=solapi` + API 키 설정
- [ ] CORS 설정 검토 (허용된 origin만)
- [ ] Rate Limiting 설정 확인 (slowapi)
- [ ] PostgreSQL 백업 전략 수립
- [ ] SSL/TLS 인증서 설정
- [ ] 모니터링 설정 (Sentry)

---

## UI/UX 디자인 (v4.1)

### 모바일 퍼스트 설계

PilaMatch는 긴급 대타 매칭 특성상 모바일 사용이 90%+ 예상되어, 모바일 퍼스트 UI로 설계되었다.

### 주요 UI 컴포넌트

| 컴포넌트 | 파일 | 설명 |
|----------|------|------|
| **Bottom Tab Bar** | `components/layout/bottom-tab-bar.tsx` | 하단 네비게이션 (탭 인디케이터 + 아이콘 하이라이트) |
| **Applicant Card** | `components/offers/applicant-card.tsx` | 지원자 카드 (Tier 뱃지, 연락처, 전화/문자 버튼) |
| **Job Creation Form** | `components/jobs/job-creation-form.tsx` | 공고 등록 폼 (6단계, 시급 범위, 핑크 긴급 버튼) |
| **Job Card** | `components/jobs/job-card.tsx` | 공고 카드 (매칭 점수, D-Day, 거리) |
| **Instructor App List** | `components/applications/instructor-application-list.tsx` | 강사 지원 현황 (매칭 완료 시 연락처 표시) |
| **Tier Badge** | `components/trust/tier-badge.tsx` | 등급 뱃지 (T1 Basic / T2 Verified / T3 Pro) |

### 핵심 UX 패턴

1. **연락처 즉시 공개**: 스튜디오가 수락하면 양측 전화번호가 즉시 표시되며, 전화/문자 버튼으로 원탭 연락 가능
2. **시급 범위 선택**: 최소/최대 시급을 버튼으로 선택, "구체적인 금액은 연락 후 조율" 안내
3. **공고 유형**: "1회 대타" (단건) / "다건 대타" (여러 회차) — 툴팁으로 설명
4. **긴급 공고**: 소프트 핑크 컬러로 긴급성 표현 (공격적 빨강 지양)
5. **공고 상태 시각화**: 좌측 컬러 바 (초록=모집중, 파랑=채용완료, 회색=마감)
6. **활성/지난 공고 분리**: 활성 공고 상단, 지난 공고 하단 (투명도 75%)

---

## 테스트 계정 (개발용)

Docker Compose로 로컬 환경 구축 후, `/auth/signup`으로 계정을 생성하거나 아래 스크립트를 사용한다.

```bash
BASE="http://localhost:8000/api/v1/auth"

# 강사 계정
curl -X POST "$BASE/signup" -H "Content-Type: application/json" \
  -d '{"email":"gangsa1@test.com","password":"Test1234","role":"instructor","display_name":"김강사"}'

# 스튜디오 계정
curl -X POST "$BASE/signup" -H "Content-Type: application/json" \
  -d '{"email":"studio1@test.com","password":"Test1234","role":"studio","business_name":"필라테스센터"}'
```

> **비밀번호 규칙**: 8자 이상, 대문자 1개 이상 포함 필수

프로필 완성 후 지원/수락 플로우를 테스트할 수 있다.

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

*Last updated: 2026-03-01 (PMF Pivot + Trust Tier System v4.1 — UI/UX 개선)*
