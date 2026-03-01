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
| **Trust-Tech** | 실명인증 기반 신뢰 -- 행동 이력이 곧 신뢰 | SMS 본인인증, 사업자인증, Trust Score (0-100), 노쇼 3-strike 정지 |
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
  |  이력, 리뷰, 거리, Trust Score, 노쇼 이력
  v
센터: 수락 (POST /applications/{id}/accept)
  |  즉시 양측 연락처 공개
  v
직접 전화/카톡으로 최종 확정
  v
수업 완료 후 상호 체크리스트 리뷰
  |  Trust Score에 반영
```

```mermaid
flowchart LR
    A[대타 공고 작성] --> B[강사 매칭 + 지원]
    B --> C[센터 수락]
    C --> D[연락처 공개]
    D --> E[직접 연락 → 수업]
    E --> F[상호 리뷰]
    F --> G[Trust Score 갱신]
```

---

## Trust-Tech: 행동 이력 = 신뢰

PilaMatch는 "돈"이 아니라 "행동"으로 신뢰를 증명한다.

| 요소 | 가중치 | 설명 |
|------|--------|------|
| 본인인증 (SMS + 사업자) | 20점 | 실명 확인 |
| 프로필 완성도 | 15점 | 자격증, 경력, 카테고리 입력 |
| 완료된 대타 이력 | 25점 | 성공적으로 수업을 마친 횟수 |
| 평균 리뷰 평점 | 15점 | 상호 체크리스트 기반 평가 |
| 자격증/인증 | 15점 | 전문 자격 보유 여부 |
| 활동 빈도 | 10점 | 지원/공고 활동 |
| 가입 기간 | 5점 | 꾸준한 참여 |
| 노쇼 감점 | -15점/회 | 3회 누적 시 계정 정지 |

**레벨 체계**: 새싹 (0-39) → 인증 (40-59) → 전문 (60-79) → 마스터 (80-100)

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
uv venv && source .venv/bin/activate
uv pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000

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

### Trust Score
| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/trust-score` | Trust Score 조회 |
| GET | `/trust-score/display` | 표시용 Trust Score (레벨, breakdown 포함) |

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

> PMF 피벗에서 프리미엄 부스트(x1.3)는 제거되었다. 매칭 점수는 순수 실력/거리 기반으로만 계산된다.

---

## Testing

총 **237개** 테스트 -- 긴급 매칭, Trust Score, 이벤트 로그, 마스킹 등.

```bash
cd backend

# 전체 테스트
uv run pytest

# 커버리지 포함
uv run pytest --cov=app --cov-report=html

# 긴급 매칭 관련 테스트
uv run pytest tests/test_urgent_matching.py -v

# Trust Score 테스트
uv run pytest tests/test_trust_score.py -v

# 특정 테스트 파일
uv run pytest tests/test_auth.py -v
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
| **Trust Score Engagement** | 본인인증 완료율 | > 70% |

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

## 비활성화 기능 (PMF 후 재활성화)

아래 기능은 코드 기반에 완전히 구현되어 있으나, PMF 피벗 기간 동안 라우터에서 비활성화되었다.
`backend/app/api/v1/router.py`에서 주석 해제하면 즉시 사용 가능하다.

| 기능 | 라우터 | 상태 |
|------|--------|------|
| 프리미엄 멤버십 (월 9,900원) | `/subscriptions` | 비활성 |
| Offer 플로우 | `/offers` | 비활성 (accept로 대체) |
| Contract 상태 머신 | `/contracts` | 비활성 |
| 실시간 채팅 (WebSocket) | `/threads` | 비활성 |
| 지원서 템플릿 (Premium) | `/templates` | 비활성 |
| 일일 사용량 제한 | `/usage` | 비활성 |

---

## License

Private - All rights reserved

---

*Last updated: 2026-03-01 (PMF Pivot: Urgent Substitute Matching)*
