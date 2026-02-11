# PilaMatch

**필라테스 & 요가 강사 매칭 플랫폼**

> "작지만 믿을 수 있는 플랫폼" - 신뢰 기반의 강사-스튜디오 매칭 서비스

---

## 목차

1. [프로젝트 개요](#프로젝트-개요)
2. [시스템 아키텍처](#시스템-아키텍처)
3. [기술 스택 상세](#기술-스택-상세)
4. [핵심 기능 및 워크플로우](#핵심-기능-및-워크플로우)
5. [데이터베이스 설계](#데이터베이스-설계)
6. [API 설계](#api-설계)
7. [보안 및 인증](#보안-및-인증)
8. [설치 및 실행](#설치-및-실행)
9. [개발 가이드](#개발-가이드)

---

## 프로젝트 개요

### 배경
기존 필라테스/요가 강사 매칭 서비스(호호요가 등)의 문제점:
- 불안정한 앱 (잦은 오류, 하얀 화면)
- 검증 시스템 부재 (가짜 프로필, 노쇼 빈번)
- 복잡한 UI (불필요한 기능 과다)

### 솔루션
**PilaMatch**는 **"신뢰"**를 핵심 가치로, 검증된 사용자 간의 안전한 거래를 보장합니다.

### 핵심 가치: 신뢰 시스템

| 기능 | 설명 | 구현 방식 |
|------|------|----------|
| **본인인증** | 실제 사용자 확인 | SMS OTP (6자리) |
| **사업자인증** | 스튜디오 실체 확인 | 사업자등록번호 검증 |
| **보증금** | 무책임 행동 방지 | 5만원 예치, 노쇼 시 3만원 차감 |
| **에스크로** | 결제 안전 보장 | 수업 완료 전까지 플랫폼 보관 |
| **노쇼 패널티** | 반복 위반자 제재 | 3회 누적 시 계정 정지 |

---

## 시스템 아키텍처

### 전체 구조

```
┌─────────────────────────────────────────────────────────────────┐
│                        Client Layer                              │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐         │
│  │  Streamlit  │    │   Mobile    │    │   Admin     │         │
│  │  (MVP Web)  │    │   (Future)  │    │  Dashboard  │         │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘         │
│         │                  │                  │                  │
│         └──────────────────┼──────────────────┘                  │
│                            │ HTTP/WebSocket                      │
├────────────────────────────┼────────────────────────────────────┤
│                     API Gateway                                  │
├────────────────────────────┼────────────────────────────────────┤
│                            ▼                                     │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    FastAPI Backend                       │    │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐       │    │
│  │  │  Auth   │ │  Jobs   │ │Contract │ │ Payment │       │    │
│  │  │ Service │ │ Service │ │ Service │ │ Service │       │    │
│  │  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘       │    │
│  │       │           │           │           │             │    │
│  │  ┌────┴───────────┴───────────┴───────────┴────┐       │    │
│  │  │           SQLAlchemy ORM (Async)            │       │    │
│  │  └─────────────────────┬───────────────────────┘       │    │
│  └────────────────────────┼────────────────────────────────┘    │
│                           │                                      │
├───────────────────────────┼──────────────────────────────────────┤
│                    Data Layer                                    │
├───────────────────────────┼──────────────────────────────────────┤
│         ┌─────────────────┼─────────────────┐                   │
│         ▼                 ▼                 ▼                   │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐           │
│  │ PostgreSQL  │   │    Redis    │   │     S3      │           │
│  │  (Primary)  │   │   (Cache)   │   │  (Storage)  │           │
│  └─────────────┘   └─────────────┘   └─────────────┘           │
│                     (Future)          (Future)                  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                    External Services                             │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐           │
│  │TossPayments │   │  SMS (NHN)  │   │  국세청 API  │           │
│  │  (Payment)  │   │   (OTP)     │   │  (Business) │           │
│  └─────────────┘   └─────────────┘   └─────────────┘           │
└─────────────────────────────────────────────────────────────────┘
```

### 컴포넌트 상세

#### Backend (FastAPI)
```
backend/app/
├── api/v1/
│   ├── endpoints/          # REST API 엔드포인트
│   │   ├── auth.py         # 인증 (signup, login, me)
│   │   ├── verification.py # 본인/사업자 인증
│   │   ├── deposit.py      # 보증금 관리
│   │   ├── instructors.py  # 강사 프로필
│   │   ├── studios.py      # 스튜디오 프로필
│   │   ├── job_posts.py    # 구인 공고 + 매칭
│   │   ├── applications.py # 지원서
│   │   ├── offers.py       # 오퍼
│   │   ├── contracts.py    # 계약 + 노쇼 신고
│   │   ├── payments.py     # 결제
│   │   ├── chat.py         # 실시간 채팅
│   │   ├── reviews.py      # 리뷰
│   │   ├── reports.py      # 신고
│   │   └── support.py      # 고객지원
│   └── router.py           # 라우터 통합
├── core/
│   ├── config.py           # 환경설정
│   ├── security.py         # JWT, 암호화
│   └── deps.py             # 의존성 주입
├── services/               # 비즈니스 로직
│   ├── auth.py             # 인증 서비스
│   ├── matching.py         # 매칭 점수 계산
│   ├── verification.py     # 인증 서비스
│   ├── deposit.py          # 보증금 서비스
│   ├── escrow.py           # 에스크로 서비스
│   ├── penalty.py          # 패널티 서비스
│   ├── contract.py         # 계약 상태 머신
│   ├── payment.py          # 결제 서비스
│   └── chat.py             # 채팅 서비스
├── models/                 # SQLAlchemy 모델
│   ├── base.py             # GUID 타입, Mixin
│   ├── user.py             # 사용자 + 인증정보
│   ├── instructor.py       # 강사 프로필
│   ├── studio.py           # 스튜디오 프로필
│   ├── job_post.py         # 구인 공고
│   ├── application.py      # 지원서
│   ├── offer.py            # 오퍼
│   ├── contract.py         # 계약
│   ├── payment.py          # 결제 + 에스크로
│   └── ...
├── schemas/                # Pydantic 스키마
└── db/
    └── session.py          # DB 세션 관리
```

---

## 기술 스택 상세

### Backend

| 기술 | 버전 | 용도 | 선택 이유 |
|------|------|------|----------|
| **Python** | 3.11+ | 런타임 | 비동기 성능 개선, 타입 힌트 강화 |
| **FastAPI** | 0.100+ | 웹 프레임워크 | 비동기 지원, 자동 문서화, 타입 검증 |
| **SQLAlchemy** | 2.0+ | ORM | 비동기 지원, 강력한 쿼리 빌더 |
| **Alembic** | 1.12+ | 마이그레이션 | SQLAlchemy 네이티브 지원 |
| **Pydantic** | 2.0+ | 데이터 검증 | FastAPI 통합, 성능 개선 |
| **uvicorn** | 0.24+ | ASGI 서버 | 고성능 비동기 서버 |
| **bcrypt** | 4.0+ | 암호화 | 업계 표준 패스워드 해싱 |
| **PyJWT** | 2.8+ | 토큰 | JWT 생성/검증 |

### Frontend (MVP)

| 기술 | 용도 | 선택 이유 |
|------|------|----------|
| **Streamlit** | UI 프레임워크 | 빠른 프로토타이핑, Python 기반 |
| **httpx** | HTTP 클라이언트 | 비동기 지원, 모던 API |

### Database

| 기술 | 용도 | 선택 이유 |
|------|------|----------|
| **PostgreSQL 15** | 프로덕션 DB | ACID, JSON 지원, 확장성 |
| **SQLite** | 테스트 DB | 설치 불필요, 빠른 테스트 |

### Infrastructure

| 기술 | 용도 |
|------|------|
| **Docker** | 컨테이너화 |
| **Docker Compose** | 멀티 컨테이너 오케스트레이션 |
| **uv** | Python 패키지 매니저 (pip 대체) |

### External Services

| 서비스 | 용도 | 상태 |
|--------|------|------|
| **TossPayments** | 결제 처리 | ✅ 연동 완료 |
| **NHN Cloud SMS** | OTP 발송 | 🔧 프로덕션 시 연동 |
| **국세청 API** | 사업자 검증 | 🔧 프로덕션 시 연동 |

---

## 핵심 기능 및 워크플로우

### 1. 사용자 가입 및 인증 플로우

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│  회원가입  │────▶│ 프로필   │────▶│ 본인인증  │────▶│ 보증금   │
│          │     │  생성    │     │ (SMS)   │     │  충전    │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
     │                                                   │
     │              ┌──────────────────┐                 │
     │              │   사업자 인증     │                 │
     │              │ (스튜디오 Only)  │                 │
     │              └──────────────────┘                 │
     │                       │                           │
     └───────────────────────┴───────────────────────────┘
                             │
                             ▼
                    ┌──────────────────┐
                    │   서비스 이용    │
                    │ (인증 배지 표시) │
                    └──────────────────┘
```

**코드 흐름:**
```python
# 1. 회원가입
POST /api/v1/auth/signup
{
    "email": "instructor@email.com",
    "password": "********",
    "role": "instructor",
    "display_name": "김필라"
}

# 2. 본인인증 요청
POST /api/v1/verification/phone/request
{"phone": "01012345678"}
# Response: {"_dev_otp": "123456"}  # 개발모드에서만

# 3. OTP 검증
POST /api/v1/verification/phone/verify
{"phone": "01012345678", "otp": "123456"}

# 4. 보증금 충전
POST /api/v1/deposit/add
{"amount": 50000}
```

### 2. 구인/구직 매칭 플로우

```
┌─────────────────────────────────────────────────────────────────┐
│                      스튜디오                                    │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
              ┌─────────────────────────┐
              │     구인 공고 등록       │
              │  - 카테고리 (필라/요가)  │
              │  - 시급, 시간, 지역      │
              │  - 필요 자격증           │
              └───────────┬─────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
        ▼                 ▼                 ▼
   ┌─────────┐      ┌─────────┐      ┌─────────┐
   │ 강사 A  │      │ 강사 B  │      │ 강사 C  │
   │ 92% 매칭│      │ 78% 매칭│      │ 45% 매칭│
   └────┬────┘      └────┬────┘      └────┬────┘
        │                │                │
        └────────────────┼────────────────┘
                         │
                         ▼
              ┌─────────────────────────┐
              │     매칭 점수 계산       │
              │  지역(30%) + 경력(25%)  │
              │  자격증(25%) + 시급(20%)│
              └─────────────────────────┘
```

**매칭 점수 계산 알고리즘:**
```python
def calculate_matching_score(instructor, job):
    scores = {}

    # 1. 지역 매칭 (30%)
    if job.region in instructor.available_regions:
        scores["region"] = 100
    else:
        scores["region"] = 0

    # 2. 경력 매칭 (25%)
    if instructor.experience_years >= job.required_experience_years:
        scores["experience"] = 100
    else:
        scores["experience"] = (instructor.experience_years / job.required_experience_years) * 100

    # 3. 자격증 매칭 (25%)
    matched = len(set(instructor.certifications) & set(job.required_certifications))
    scores["certifications"] = (matched / len(job.required_certifications)) * 100

    # 4. 시급 매칭 (20%)
    if instructor.hourly_rate_min <= job.hourly_rate <= instructor.hourly_rate_max:
        scores["rate"] = 100

    # 가중 평균
    total = (scores["region"] * 0.30 +
             scores["experience"] * 0.25 +
             scores["certifications"] * 0.25 +
             scores["rate"] * 0.20)

    return {"total": total, "breakdown": scores}
```

### 3. 계약 상태 머신

```
                    ┌─────────────────┐
                    │    CONFIRMED    │ ◀── 오퍼 수락 시 생성
                    │    (확정됨)     │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              │              ▼
     ┌─────────────┐         │     ┌─────────────┐
     │  CANCELLED  │         │     │  결제 완료   │
     │   (취소)    │         │     │ (에스크로)  │
     └─────────────┘         │     └──────┬──────┘
              ▲              │            │
              │              ▼            ▼
              │     ┌─────────────────────────┐
              │     │      IN_PROGRESS        │
              ├─────│       (진행중)          │
              │     └───────────┬─────────────┘
              │                 │
              │     ┌───────────┼───────────┐
              │     │           │           │
              ▼     ▼           │           ▼
     ┌─────────────┐            │  ┌─────────────────┐
     │  CANCELLED  │            │  │    COMPLETED    │
     │ + 환불처리   │            │  │    (완료)       │
     └─────────────┘            │  │  + 강사 정산    │
                                │  └─────────────────┘
                                │           │
                                ▼           ▼
                    ┌─────────────────────────────┐
                    │        노쇼 신고            │
                    │  - 보증금 3만원 차감         │
                    │  - 3회 누적 시 계정 정지     │
                    └─────────────────────────────┘
```

**상태 전이 규칙:**
```python
VALID_TRANSITIONS = {
    ContractStatus.CONFIRMED: {
        ContractStatus.IN_PROGRESS,  # 결제 완료 후
        ContractStatus.CANCELLED,    # 취소
    },
    ContractStatus.IN_PROGRESS: {
        ContractStatus.COMPLETED,    # 수업 완료
        ContractStatus.CANCELLED,    # 취소 (환불)
    },
    ContractStatus.COMPLETED: set(),   # 최종 상태
    ContractStatus.CANCELLED: set(),   # 최종 상태
}
```

### 4. 에스크로 결제 플로우

```
┌──────────┐                    ┌──────────┐                    ┌──────────┐
│ 스튜디오  │                    │ 플랫폼   │                    │  강사    │
└────┬─────┘                    └────┬─────┘                    └────┬─────┘
     │                               │                               │
     │  1. 계약 확정 + 결제          │                               │
     │──────────────────────────────▶│                               │
     │                               │                               │
     │                    ┌──────────┴──────────┐                    │
     │                    │ 에스크로 상태: HELD │                    │
     │                    │ (플랫폼이 보관)     │                    │
     │                    └──────────┬──────────┘                    │
     │                               │                               │
     │  2. 수업 진행                 │                               │
     │◀ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ┼ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─ ─▶│
     │                               │                               │
     │  3. 수업 완료 확인            │                               │
     │──────────────────────────────▶│                               │
     │                               │                               │
     │                    ┌──────────┴──────────┐                    │
     │                    │ 에스크로: RELEASED  │                    │
     │                    │ 플랫폼 수수료: 5%   │                    │
     │                    └──────────┬──────────┘                    │
     │                               │                               │
     │                               │  4. 정산 (95%)                │
     │                               │──────────────────────────────▶│
     │                               │                               │
     ▼                               ▼                               ▼

─────────────────────────── 취소 시나리오 ───────────────────────────

     │  취소 요청                    │                               │
     │──────────────────────────────▶│                               │
     │                               │                               │
     │                    ┌──────────┴──────────┐                    │
     │                    │ 에스크로: REFUNDED  │                    │
     │                    │ 전액 환불 (정상취소)│                    │
     │                    │ or                  │                    │
     │                    │ 70% 환불 (노쇼)     │                    │
     │                    └──────────┬──────────┘                    │
     │                               │                               │
     │  환불금 수령                  │                               │
     │◀──────────────────────────────│                               │
     │                               │                               │
```

### 5. 노쇼 패널티 시스템

```
┌─────────────────────────────────────────────────────────────────┐
│                      노쇼 신고 프로세스                          │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
              ┌─────────────────────────┐
              │    노쇼 신고 접수       │
              │ POST /contracts/{id}/   │
              │      report-no-show     │
              └───────────┬─────────────┘
                          │
                          ▼
              ┌─────────────────────────┐
              │   패널티 자동 적용      │
              │ • no_show_count += 1    │
              │ • 보증금 -30,000원      │
              │ • 계약 자동 취소        │
              └───────────┬─────────────┘
                          │
           ┌──────────────┼──────────────┐
           │              │              │
           ▼              ▼              ▼
      ┌─────────┐   ┌─────────┐   ┌─────────┐
      │ 1회차   │   │ 2회차   │   │ 3회차   │
      │ 경고    │   │ 경고    │   │ 정지    │
      │ 잔여2회 │   │ 잔여1회 │   │ 계정차단│
      └─────────┘   └─────────┘   └─────────┘
```

---

## 데이터베이스 설계

### ERD (Entity Relationship Diagram)

```
┌─────────────────┐       ┌─────────────────┐
│      users      │       │instructor_profiles│
├─────────────────┤       ├─────────────────┤
│ id (PK)         │──┐    │ id (PK)         │
│ email           │  │    │ user_id (FK)────│──┐
│ hashed_password │  │    │ display_name    │  │
│ role            │  │    │ bio             │  │
│ is_active       │  │    │ certifications  │  │
│ phone           │  │    │ experience_years│  │
│ phone_verified  │  │    │ hourly_rate_min │  │
│ identity_verified│ │    │ hourly_rate_max │  │
│ business_number │  │    │ available_regions│ │
│ business_verified│ │    │ rating_average  │  │
│ deposit_balance │  │    └─────────────────┘  │
│ no_show_count   │  │                         │
│ is_suspended    │  │    ┌─────────────────┐  │
└─────────────────┘  │    │ studio_profiles │  │
                     │    ├─────────────────┤  │
                     │    │ id (PK)         │  │
                     └────│ user_id (FK)────│──┘
                          │ business_name   │
                          │ address         │
                          │ region          │
                          │ rating_average  │
                          └────────┬────────┘
                                   │
                          ┌────────┴────────┐
                          ▼                 ▼
              ┌─────────────────┐  ┌─────────────────┐
              │    job_posts    │  │   applications  │
              ├─────────────────┤  ├─────────────────┤
              │ id (PK)         │  │ id (PK)         │
              │ studio_id (FK)──│  │ job_post_id(FK)─│
              │ title           │  │ instructor_id(FK)│
              │ category        │  │ status          │
              │ job_type        │  │ cover_letter    │
              │ hourly_rate     │  └────────┬────────┘
              │ date            │           │
              │ required_certs  │           ▼
              │ status          │  ┌─────────────────┐
              └─────────────────┘  │     offers      │
                                   ├─────────────────┤
                                   │ id (PK)         │
                                   │ application_id  │
                                   │ studio_id       │
                                   │ instructor_id   │
                                   │ proposed_rate   │
                                   │ status          │
                                   └────────┬────────┘
                                            │
                                            ▼
                                   ┌─────────────────┐
                                   │    contracts    │
                                   ├─────────────────┤
                                   │ id (PK)         │
                                   │ offer_id (FK)   │
                                   │ studio_id       │
                                   │ instructor_id   │
                                   │ status          │──▶ CONFIRMED
                                   │ total_amount    │     IN_PROGRESS
                                   │ date            │     COMPLETED
                                   │ cancellation_   │     CANCELLED
                                   │   reason        │
                                   └────────┬────────┘
                                            │
                              ┌─────────────┼─────────────┐
                              ▼             ▼             ▼
                     ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
                     │  payments   │ │   payouts   │ │   reviews   │
                     ├─────────────┤ ├─────────────┤ ├─────────────┤
                     │ id          │ │ id          │ │ id          │
                     │ contract_id │ │ contract_id │ │ contract_id │
                     │ amount      │ │ amount      │ │ rating      │
                     │ status      │ │ status      │ │ comment     │
                     │ escrow_     │ └─────────────┘ └─────────────┘
                     │   status    │
                     │ payment_key │
                     └─────────────┘
```

### 주요 테이블 컬럼

#### users
```sql
CREATE TABLE users (
    id              VARCHAR(36) PRIMARY KEY,
    email           VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role            VARCHAR(20) NOT NULL,  -- 'instructor' | 'studio'
    is_active       BOOLEAN DEFAULT TRUE,
    is_verified     BOOLEAN DEFAULT FALSE,

    -- 인증 정보
    phone           VARCHAR(20),
    phone_verified  BOOLEAN DEFAULT FALSE,
    identity_verified BOOLEAN DEFAULT FALSE,
    business_number VARCHAR(20),
    business_verified BOOLEAN DEFAULT FALSE,

    -- 보증금
    deposit_balance  NUMERIC(10,2) DEFAULT 0,
    deposit_required NUMERIC(10,2) DEFAULT 50000,

    -- 패널티
    no_show_count   INTEGER DEFAULT 0,
    is_suspended    BOOLEAN DEFAULT FALSE,

    created_at      TIMESTAMP NOT NULL,
    updated_at      TIMESTAMP NOT NULL
);
```

#### payments (에스크로)
```sql
CREATE TABLE payments (
    id              VARCHAR(36) PRIMARY KEY,
    contract_id     VARCHAR(36) REFERENCES contracts(id),
    payer_user_id   VARCHAR(36) REFERENCES users(id),
    amount          NUMERIC(10,2) NOT NULL,
    platform_fee    NUMERIC(10,2) DEFAULT 0,
    status          VARCHAR(20) NOT NULL,  -- PENDING | COMPLETED | FAILED | REFUNDED
    escrow_status   VARCHAR(20) DEFAULT 'HELD',  -- HELD | RELEASED | REFUNDED
    payment_key     VARCHAR(200) UNIQUE,  -- TossPayments key
    order_id        VARCHAR(200) UNIQUE NOT NULL,
    created_at      TIMESTAMP NOT NULL,
    updated_at      TIMESTAMP NOT NULL
);
```

---

## API 설계

### RESTful 원칙

| Method | 용도 | 예시 |
|--------|------|------|
| GET | 조회 | `GET /job-posts` |
| POST | 생성 | `POST /job-posts` |
| PUT | 전체 수정 | `PUT /job-posts/{id}` |
| PATCH | 부분 수정 | `PATCH /users/me` |
| DELETE | 삭제 | `DELETE /job-posts/{id}` |

### 응답 형식

**성공 응답:**
```json
{
    "id": "uuid",
    "email": "user@example.com",
    "role": "instructor",
    "created_at": "2026-02-10T12:00:00Z"
}
```

**에러 응답:**
```json
{
    "detail": {
        "code": "INVALID_CREDENTIALS",
        "message": "Invalid email or password"
    }
}
```

**페이지네이션:**
```json
{
    "items": [...],
    "total": 100,
    "page": 1,
    "page_size": 20
}
```

### 주요 API 엔드포인트

#### 인증 (Auth)
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/auth/signup` | 회원가입 |
| POST | `/auth/login` | 로그인 → JWT 발급 |
| GET | `/auth/me` | 내 정보 조회 |

#### 인증 (Verification)
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/verification/phone/request` | SMS OTP 요청 |
| POST | `/verification/phone/verify` | OTP 검증 |
| POST | `/verification/business/verify` | 사업자 인증 |
| GET | `/verification/status` | 인증 상태 조회 |

#### 보증금 (Deposit)
| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/deposit/status` | 보증금 현황 |
| POST | `/deposit/add` | 보증금 충전 |
| POST | `/deposit/refund` | 보증금 환불 요청 |

#### 공고 (Job Posts)
| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/job-posts` | 공고 목록 (필터링) |
| GET | `/job-posts/for-me/with-matching` | 매칭 점수 포함 목록 |
| POST | `/job-posts` | 공고 등록 (스튜디오) |
| GET | `/job-posts/{id}` | 공고 상세 |

#### 계약 (Contracts)
| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/contracts/from-offer/{offer_id}` | 계약 생성 |
| GET | `/contracts/me` | 내 계약 목록 |
| POST | `/contracts/{id}/set-in-progress` | 진행 시작 |
| POST | `/contracts/{id}/complete` | 완료 처리 |
| POST | `/contracts/{id}/cancel` | 취소 |
| POST | `/contracts/{id}/report-no-show` | 노쇼 신고 |

---

## 보안 및 인증

### JWT 인증 흐름

```
┌──────────┐                    ┌──────────┐                    ┌──────────┐
│  Client  │                    │  Server  │                    │    DB    │
└────┬─────┘                    └────┬─────┘                    └────┬─────┘
     │                               │                               │
     │  POST /auth/login             │                               │
     │  {email, password}            │                               │
     │──────────────────────────────▶│                               │
     │                               │   SELECT user WHERE email    │
     │                               │──────────────────────────────▶│
     │                               │                               │
     │                               │   user data                   │
     │                               │◀──────────────────────────────│
     │                               │                               │
     │                               │  bcrypt.verify(password)      │
     │                               │  jwt.encode({sub: user_id})   │
     │                               │                               │
     │  {access_token: "eyJ..."}     │                               │
     │◀──────────────────────────────│                               │
     │                               │                               │
     │  GET /auth/me                 │                               │
     │  Authorization: Bearer eyJ... │                               │
     │──────────────────────────────▶│                               │
     │                               │   jwt.decode(token)           │
     │                               │   SELECT user WHERE id        │
     │                               │──────────────────────────────▶│
     │                               │◀──────────────────────────────│
     │  {user data}                  │                               │
     │◀──────────────────────────────│                               │
```

### 비밀번호 암호화

```python
# bcrypt 해싱 (salt 자동 생성)
hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())

# 검증
bcrypt.checkpw(password.encode(), hashed)
```

### 권한 체크

```python
# 역할 기반 접근 제어
@router.post("/job-posts")
async def create_job_post(
    current_user: User = Depends(require_role(UserRole.STUDIO))  # 스튜디오만
):
    ...
```

---

## 설치 및 실행

### 사전 요구사항

- Docker & Docker Compose
- Python 3.11+ (로컬 개발 시)
- uv (Python 패키지 매니저)

### Docker 실행 (권장)

```bash
# 1. 저장소 클론
git clone https://github.com/your-repo/PilaMatch.git
cd PilaMatch

# 2. 환경변수 설정
cp .env.example .env
# .env 파일 수정

# 3. 서비스 시작
docker-compose up -d --build

# 4. 로그 확인
docker-compose logs -f backend

# 5. 접속
# API 문서: http://localhost:8000/api/v1/docs
# Frontend: http://localhost:8501
```

### 로컬 개발

```bash
# Backend
cd backend
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload

# Frontend (새 터미널)
cd frontend
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
streamlit run app.py
```

### 환경 변수

```bash
# Database
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/pilamatch
DATABASE_URL_SYNC=postgresql://postgres:password@localhost:5432/pilamatch

# Security
SECRET_KEY=your-super-secret-key-change-in-production

# TossPayments
TOSS_CLIENT_KEY=test_ck_...
TOSS_SECRET_KEY=test_sk_...

# Debug
DEBUG=true
```

---

## 개발 가이드

### 코드 컨벤션

- **Python**: PEP 8, Black formatter
- **Type Hints**: 모든 함수에 타입 힌트 필수
- **Docstrings**: Google style

### Git 컨벤션

```
feat: 새로운 기능 추가
fix: 버그 수정
docs: 문서 변경
refactor: 코드 리팩토링
test: 테스트 추가/수정
chore: 빌드, 설정 변경
```

### 세션 문서화 규칙

> **세션의 80% 소모 시, `docs/summary_YYYYMMDD.md` 자동 생성**

### DB 호환성 규칙

| 문제 | 해결책 |
|------|--------|
| UUID 타입 | `GUID` 커스텀 타입 (CHAR(36)) |
| Enum 타입 | `String(20)` 사용 |
| Array 타입 | `JSON` 사용 |

### 테스트

```bash
# 전체 테스트
uv run pytest

# 커버리지
uv run pytest --cov=app --cov-report=html

# 특정 테스트
uv run pytest tests/test_auth.py -v
```

---

## 다이어그램 (Mermaid)

> GitHub, GitLab, Notion 등에서 자동 렌더링됩니다.

### 시스템 아키텍처

```mermaid
flowchart TB
    subgraph Client["Client Layer"]
        Web["Streamlit<br/>(MVP Web)"]
        Mobile["Mobile App<br/>(Future)"]
        Admin["Admin Dashboard<br/>(Future)"]
    end

    subgraph API["API Layer"]
        Gateway["API Gateway"]
        subgraph FastAPI["FastAPI Backend"]
            Auth["Auth<br/>Service"]
            Jobs["Jobs<br/>Service"]
            Contract["Contract<br/>Service"]
            Payment["Payment<br/>Service"]
            Matching["Matching<br/>Service"]
        end
    end

    subgraph Data["Data Layer"]
        PostgreSQL[(PostgreSQL)]
        Redis[(Redis<br/>Cache)]
        S3[(S3<br/>Storage)]
    end

    subgraph External["External Services"]
        Toss["TossPayments"]
        SMS["NHN Cloud SMS"]
        NTS["국세청 API"]
    end

    Web & Mobile & Admin --> Gateway
    Gateway --> FastAPI
    Auth & Jobs & Contract & Payment & Matching --> PostgreSQL
    Payment --> Toss
    Auth --> SMS
    Auth --> NTS
```

### 사용자 가입 플로우

```mermaid
flowchart LR
    A[회원가입] --> B[프로필 생성]
    B --> C{역할}
    C -->|강사| D[본인인증<br/>SMS OTP]
    C -->|스튜디오| E[본인인증<br/>SMS OTP]
    E --> F[사업자인증]
    D --> G[보증금 충전<br/>50,000원]
    F --> G
    G --> H[서비스 이용<br/>인증 배지 표시]
```

### 매칭 알고리즘

```mermaid
pie title 매칭 점수 가중치
    "지역 일치" : 30
    "경력 충족" : 25
    "자격증 보유" : 25
    "희망 시급" : 20
```

### 계약 상태 머신

```mermaid
stateDiagram-v2
    [*] --> CONFIRMED: 오퍼 수락

    CONFIRMED --> IN_PROGRESS: 결제 완료
    CONFIRMED --> CANCELLED: 취소 요청

    IN_PROGRESS --> COMPLETED: 수업 완료
    IN_PROGRESS --> CANCELLED: 취소/노쇼

    COMPLETED --> [*]
    CANCELLED --> [*]

    note right of CONFIRMED
        에스크로: HELD
        (플랫폼 보관)
    end note

    note right of COMPLETED
        에스크로: RELEASED
        (강사 정산 95%)
    end note

    note right of CANCELLED
        에스크로: REFUNDED
        (스튜디오 환불)
    end note
```

### 에스크로 결제 플로우

```mermaid
sequenceDiagram
    participant S as 스튜디오
    participant P as PilaMatch
    participant T as TossPayments
    participant I as 강사

    S->>P: 1. 계약 확정 + 결제 요청
    P->>T: 2. 결제 처리
    T-->>P: 3. 결제 완료 (payment_key)
    P->>P: 4. 에스크로 HELD

    Note over S,I: 수업 진행

    S->>P: 5. 수업 완료 확인
    P->>P: 6. 에스크로 RELEASED
    P->>I: 7. 정산 (금액 - 5% 수수료)

    rect rgb(255, 200, 200)
        Note over S,I: 취소 시나리오
        S->>P: 취소 요청
        P->>P: 에스크로 REFUNDED
        P->>S: 환불 처리
    end
```

### 노쇼 패널티 시스템

```mermaid
flowchart TD
    A[노쇼 신고 접수] --> B[패널티 적용]
    B --> C{no_show_count}

    C -->|1회| D[경고<br/>보증금 -3만원<br/>잔여 2회]
    C -->|2회| E[경고<br/>보증금 -3만원<br/>잔여 1회]
    C -->|3회| F[계정 정지<br/>is_suspended = true]

    D --> G[서비스 계속]
    E --> G
    F --> H[서비스 이용 불가]

    style F fill:#ff6b6b
    style H fill:#ff6b6b
```

### ERD (Entity Relationship)

```mermaid
erDiagram
    users ||--o| instructor_profiles : has
    users ||--o| studio_profiles : has

    studio_profiles ||--o{ job_posts : creates
    job_posts ||--o{ applications : receives
    instructor_profiles ||--o{ applications : submits

    applications ||--o| offers : generates
    offers ||--o| contracts : creates

    contracts ||--o{ payments : has
    contracts ||--o{ reviews : has

    users {
        uuid id PK
        string email UK
        string role
        boolean phone_verified
        boolean business_verified
        decimal deposit_balance
        int no_show_count
        boolean is_suspended
    }

    instructor_profiles {
        uuid id PK
        uuid user_id FK
        string display_name
        json certifications
        int experience_years
        decimal hourly_rate_min
        decimal hourly_rate_max
    }

    studio_profiles {
        uuid id PK
        uuid user_id FK
        string business_name
        string region
        string business_number
    }

    job_posts {
        uuid id PK
        uuid studio_id FK
        string title
        string category
        decimal hourly_rate
        string status
    }

    contracts {
        uuid id PK
        uuid studio_id FK
        uuid instructor_id FK
        string status
        decimal total_amount
    }

    payments {
        uuid id PK
        uuid contract_id FK
        decimal amount
        string status
        string escrow_status
    }
```

### 전체 서비스 플로우

```mermaid
flowchart TB
    subgraph Registration["1. 가입/인증"]
        R1[회원가입] --> R2[본인인증]
        R2 --> R3[보증금 충전]
    end

    subgraph Matching["2. 매칭"]
        M1[공고 등록] --> M2[매칭 점수 계산]
        M2 --> M3[지원서 제출]
        M3 --> M4[오퍼 전송]
        M4 --> M5[오퍼 수락]
    end

    subgraph Contract["3. 계약"]
        C1[계약 생성] --> C2[에스크로 결제]
        C2 --> C3[수업 진행]
        C3 --> C4{결과}
        C4 -->|완료| C5[강사 정산]
        C4 -->|취소| C6[환불 처리]
        C4 -->|노쇼| C7[패널티 적용]
    end

    subgraph Review["4. 리뷰"]
        V1[리뷰 작성] --> V2[평점 갱신]
    end

    Registration --> Matching
    Matching --> Contract
    Contract --> Review
```

---

## 라이선스

Private - All rights reserved

---

## 문의

- 개발 문서: [CLAUDE.md](./CLAUDE.md)
- 세션 기록: [docs/](./docs/)

---

*Last updated: 2026-02-10*
