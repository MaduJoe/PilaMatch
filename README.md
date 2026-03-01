# PilaMatch

**필라테스/요가 강사와 스튜디오(센터) 매칭 플랫폼**

> "작지만 믿을 수 있는 플랫폼" - 신뢰 기반의 강사-스튜디오 매칭 서비스

---

## 목차

1. [프로젝트 개요](#프로젝트-개요)
2. [시스템 아키텍처](#시스템-아키텍처)
3. [기술 스택 상세](#기술-스택-상세)
4. [핵심 기능 및 워크플로우](#핵심-기능-및-워크플로우)
5. [프리미엄 멤버십 시스템](#프리미엄-멤버십-시스템)
6. [데이터베이스 설계](#데이터베이스-설계)
7. [API 설계](#api-설계)
8. [보안 및 인증](#보안-및-인증)
9. [설치 및 실행](#설치-및-실행)
10. [테스트](#테스트)
11. [개발 가이드](#개발-가이드)

---

## 프로젝트 개요

### 배경
기존 필라테스/요가 강사 매칭 서비스(호호요가 등)의 문제점:
- 불안정한 앱 (잦은 오류, 하얀 화면)
- 검증 시스템 부재 (가짜 프로필, 노쇼 빈번)
- 복잡한 UI (불필요한 기능 과다)

### 솔루션
**PilaMatch**는 **"신뢰"**를 핵심 가치로, 검증된 사용자 간의 안전한 거래를 보장합니다.

### 현재 상태
MVP Complete - 전체 신뢰 기능 및 프리미엄 멤버십 구현 완료:
- JWT 기반 인증 (Access + Refresh Token)
- 본인인증 (SMS OTP) + 사업자인증
- 노쇼 패널티 시스템 (Trust Score 감점, 3회 정지)
- 4-Factor 매칭 알고리즘
- 계약 상태 머신 + 이벤트 로깅
- 프리미엄 멤버십 (월 9,900원)
- 실시간 채팅 (WebSocket)
- Trust Score 시스템 (0-100)

### 핵심 가치: 신뢰 시스템

| 기능 | 설명 | 구현 방식 |
|------|------|----------|
| **본인인증** | 실제 사용자 확인 | SMS OTP 6자리 (Solapi + Redis) |
| **사업자인증** | 스튜디오 실체 확인 | 국세청 API + 체크섬 검증 |
| **노쇼 패널티** | 반복 위반자 제재 | Trust Score 감점, 3회 누적 시 계정 정지 |
| **Trust Score** | 종합 신뢰도 지표 | 0-100점 (인증, 활동, 리뷰 기반) |
| **프리미엄 멤버십** | 추가 혜택 제공 | 월 9,900원, 매칭 부스트 등 |

---

## 시스템 아키텍처

### 전체 구조

```
+-------------------------------------------------------------------+
|                        Client Layer                                |
+-------------------------------------------------------------------+
|  +--------------+    +--------------+    +--------------+          |
|  |   Next.js    |    |    Mobile    |    |    Admin     |          |
|  |  (Web App)   |    |   (Future)   |    |  Dashboard   |          |
|  +------+-------+    +------+-------+    +------+-------+          |
|         |                   |                   |                   |
|         +-------------------+-------------------+                   |
|                             | HTTP/WebSocket                        |
+-----------------------------+---------------------------------------+
|                      API Gateway (BFF)                              |
+-----------------------------+---------------------------------------+
|                             v                                       |
|  +----------------------------------------------------------+     |
|  |                    FastAPI Backend                         |     |
|  |  +----------+ +----------+ +----------+ +----------+      |     |
|  |  |   Auth   | |   Jobs   | | Contract | | Review   |      |     |
|  |  | Service  | | Service  | | Service  | | Service  |      |     |
|  |  +----+-----+ +----+-----+ +----+-----+ +----+-----+      |     |
|  |       |             |           |            |              |     |
|  |  +----+-----+ +----+-----+ +---+------+ +---+-------+     |     |
|  |  | Matching | |   Chat   | | Penalty  | | TrustScore|     |     |
|  |  | Service  | | Service  | | Service  | | Service   |     |     |
|  |  +----------+ +----------+ +----------+ +-----------+     |     |
|  |       |             |           |            |              |     |
|  |  +----+-------------+-----------+------------+----+        |     |
|  |  |            SQLAlchemy ORM (Async)              |        |     |
|  |  +------------------------+-----------------------+        |     |
|  +---------------------------+----------------------------+   |     |
|                              |                                |     |
+------------------------------+--------------------------------+-----+
|                        Data Layer                                    |
+------------------------------+---------------------------------------+
|         +--------------------+--------------------+                  |
|         v                    v                    v                  |
|  +--------------+     +--------------+     +--------------+          |
|  | PostgreSQL   |     |    Redis     |     |  S3 / Local  |          |
|  |   15-alpine  |     |   7-alpine   |     |   Storage    |          |
|  |  (Primary)   |     | (OTP Cache)  |     |   (Files)    |          |
|  +--------------+     +--------------+     +--------------+          |
+----------------------------------------------------------------------+

+----------------------------------------------------------------------+
|                      External Services                                |
+----------------------------------------------------------------------+
|  +--------------+     +--------------+     +--------------+           |
|  | TossPayments |     | Solapi (SMS) |     |  국세청 API   |           |
|  | (구독 결제)  |     |  (OTP 발송)   |     | (사업자 검증) |           |
|  +--------------+     +--------------+     +--------------+           |
+----------------------------------------------------------------------+
```

### Backend 프로젝트 구조 (19 Endpoints, 26 Services)

```
backend/app/
├── api/v1/
│   ├── endpoints/              # 19 REST API endpoints
│   │   ├── auth.py             # 인증 (signup, login, refresh, password reset)
│   │   ├── verification.py     # 본인/사업자 인증
│   │   ├── subscription.py     # 프리미엄 구독
│   │   ├── profiles.py         # 사용자 프로필
│   │   ├── trust.py            # Trust Score
│   │   ├── instructors.py      # 강사 프로필
│   │   ├── studios.py          # 스튜디오 프로필
│   │   ├── job_posts.py        # 구인 공고 + 매칭
│   │   ├── applications.py     # 지원서
│   │   ├── offers.py           # 오퍼
│   │   ├── contracts.py        # 계약 + 노쇼 신고
│   │   ├── chat.py             # 실시간 채팅 (WebSocket)
│   │   ├── reviews.py          # 리뷰
│   │   ├── reports.py          # 신고/차단
│   │   ├── support.py          # 고객지원
│   │   ├── templates.py        # 지원서 템플릿 (Premium)
│   │   ├── usage.py            # 일일 사용량
│   │   └── notifications.py    # 알림
│   └── router.py               # 라우터 통합
├── core/
│   ├── config.py               # Pydantic Settings
│   ├── security.py             # JWT (python-jose), bcrypt
│   ├── deps.py                 # Auth dependencies, role check
│   └── logging.py              # structlog 설정
├── services/                   # 26 business logic services
│   ├── auth.py                 # 인증 서비스
│   ├── verification.py         # 인증 (Redis OTP)
│   ├── sms.py                  # SMS 전송 (Solapi/Mock)
│   ├── nts_client.py           # 국세청 API 클라이언트
│   ├── matching.py             # 매칭 점수 계산
│   ├── penalty.py              # 패널티 서비스
│   ├── contract.py             # 계약 상태 머신
│   ├── subscription.py         # 프리미엄 구독
│   ├── trust_score.py          # Trust Score 계산
│   ├── daily_usage.py          # 일일 사용량 추적
│   ├── profile_completeness.py # 프로필 완성도
│   ├── application.py          # 지원 서비스
│   ├── application_template.py # 템플릿 서비스
│   ├── offer.py                # 오퍼 서비스
│   ├── instructor.py           # 강사 서비스
│   ├── studio.py               # 스튜디오 서비스
│   ├── job_post.py             # 공고 서비스
│   ├── chat.py                 # 채팅 서비스
│   ├── review.py               # 리뷰 서비스
│   ├── report.py               # 신고 서비스
│   ├── support.py              # 고객지원 서비스
│   ├── notification.py         # 알림 서비스
│   ├── dispute.py              # 분쟁 해결
│   ├── file_upload.py          # 파일 업로드 (Local/S3)
│   ├── email.py                # 이메일 서비스
│   └── account_deletion.py     # 계정 삭제 (30일 유예)
├── models/                     # 23 SQLAlchemy models
│   ├── base.py                 # GUID type, Mixins
│   ├── enums.py                # All enums
│   ├── user.py
│   ├── instructor.py
│   ├── studio.py
│   ├── job_post.py
│   ├── application.py
│   ├── offer.py
│   ├── contract.py             # + ContractEventLog
│   ├── payment.py              # + Payout
│   ├── payment_cancellation.py
│   ├── webhook_event.py
│   ├── chat.py                 # Thread + Message
│   ├── notification.py         # + DeviceToken
│   ├── device_token.py
│   ├── review.py
│   ├── report.py               # + Block
│   ├── support.py
│   ├── dispute.py
│   ├── subscription.py         # + Payment + History
│   ├── daily_usage.py
│   └── application_template.py
├── schemas/                    # 15 Pydantic schemas
└── db/
    └── session.py              # DB 세션 관리
```

### Frontend 프로젝트 구조 (Next.js)

```
frontend-next/
├── src/
│   ├── app/
│   │   ├── login/              # 로그인
│   │   ├── signup/             # 회원가입
│   │   ├── forgot-password/    # 비밀번호 찾기
│   │   ├── reset-password/     # 비밀번호 재설정
│   │   ├── (app)/steps/        # 보호된 앱 라우트
│   │   │   ├── profile/        # 프로필 설정
│   │   │   ├── jobs/           # 공고 탐색/등록
│   │   │   ├── offers/         # 오퍼 관리
│   │   │   ├── contracts/      # 계약 관리
│   │   │   └── complete/       # 완료 및 리뷰
│   │   ├── (app)/notifications/ # 알림
│   │   ├── (app)/settings/     # 계정 설정
│   │   ├── payment/            # 결제 결과
│   │   ├── billing/            # 빌링 결과
│   │   ├── privacy/            # 개인정보처리방침
│   │   ├── terms/              # 이용약관
│   │   └── refund/             # 환불정책
│   ├── components/             # 63 React components
│   │   ├── ui/                 # 22 shadcn/ui components
│   │   ├── layout/             # Header, StepProgress, StepNavigation
│   │   ├── profile/            # 8 profile components
│   │   ├── jobs/               # 5 job components (Kakao Map)
│   │   ├── offers/             # 6 offer components
│   │   ├── contracts/          # 4 contract components
│   │   ├── reviews/            # 6 review components
│   │   ├── payment/            # 2 payment components (구독 전용)
│   │   └── notification/       # 1 notification component
│   ├── lib/
│   │   ├── api-client.ts       # Typed API client
│   │   ├── api-types.ts        # Full type definitions
│   │   ├── validators.ts       # Zod schemas
│   │   └── constants.ts        # App constants
│   ├── hooks/                  # Custom React hooks
│   ├── stores/                 # Zustand stores (auth)
│   ├── providers/              # Context providers (auth, query, toast)
│   └── middleware.ts           # Auth middleware (httpOnly cookie)
├── __tests__/                  # 7 Vitest test files
├── Dockerfile                  # 3-stage multi-build
└── package.json
```

---

## 기술 스택 상세

### Backend

| 기술 | 버전 | 용도 | 선택 이유 |
|------|------|------|----------|
| **Python** | 3.11+ | 런타임 | 비동기 성능 개선, 타입 힌트 강화 |
| **FastAPI** | 0.109+ | 웹 프레임워크 | 비동기 지원, 자동 문서화, 타입 검증 |
| **SQLAlchemy** | 2.0.25 | ORM (async) | 비동기 지원, 강력한 쿼리 빌더 |
| **Alembic** | 1.13+ | 마이그레이션 | SQLAlchemy 네이티브 지원 |
| **Pydantic** | 2.5+ | 데이터 검증 | FastAPI 통합, 성능 개선 |
| **uvicorn** | 0.27+ | ASGI 서버 | 고성능 비동기 서버 |
| **python-jose** | 3.3.0 | JWT | 토큰 생성/검증, 다양한 알고리즘 지원 |
| **passlib + bcrypt** | 4.1+ | 암호화 | 업계 표준 패스워드 해싱 |
| **httpx** | 0.26+ | HTTP 클라이언트 | 비동기 지원, 외부 API 연동 |
| **websockets** | 12.0 | WebSocket | 실시간 채팅 |
| **slowapi** | 0.1.9 | Rate Limiting | API 남용 방지 |
| **structlog** | 24.1.0 | 구조화된 로깅 | JSON 로그, 컨텍스트 기반 |

### Frontend

| 기술 | 버전 | 용도 | 선택 이유 |
|------|------|------|----------|
| **Next.js** | 16.1.6 | React 프레임워크 | SSR/SSG, App Router, BFF 패턴 |
| **React** | 19.2.3 | UI 라이브러리 | 컴포넌트 기반, 생태계 |
| **TypeScript** | 5 | 타입 안전성 | 컴파일 타임 에러 감지 |
| **Tailwind CSS** | 4 | 스타일링 | 유틸리티 우선, 빠른 개발 |
| **shadcn/ui (Radix)** | - | UI 컴포넌트 | 접근성, 커스터마이징 |
| **Zustand** | 5.0.11 | 상태 관리 | 경량, 보일러플레이트 최소화 |
| **TanStack Query** | 5.90+ | API 캐싱 | 서버 상태 관리, 자동 갱신 |
| **react-hook-form + Zod** | - | 폼 검증 | 성능 최적화, 스키마 기반 검증 |
| **@tosspayments/payment-sdk** | 2.3.0 | 구독 결제 | TossPayments 공식 SDK |

### Database

| 기술 | 용도 | 선택 이유 |
|------|------|----------|
| **PostgreSQL 15** | 프로덕션 DB | ACID, JSON 지원, 확장성 |
| **SQLite** | 테스트 DB | 설치 불필요, 빠른 테스트 |
| **Redis 7** | OTP 캐싱 + 세션 | TTL 기반 만료, in-memory fallback 포함 |

### Infrastructure

| 기술 | 용도 |
|------|------|
| **Docker + Docker Compose** | 컨테이너화 (4 services) |
| **GitHub Actions** | CI/CD (lint -> test -> build) |
| **uv** | Python 패키지 매니저 |
| **pnpm** | Node 패키지 매니저 |

### External Services

| 서비스 | 용도 | 상태 |
|--------|------|------|
| **TossPayments** | 프리미엄 구독 결제 | 연동 완료 |
| **Solapi (CoolSMS v4)** | SMS OTP 발송 | 연동 완료 |
| **국세청 API** | 사업자등록번호 검증 | 연동 완료 (체크섬 + API) |
| **Redis** | OTP 캐싱 | 구현 완료 (in-memory fallback 포함) |
| **S3** | 파일 스토리지 | 구현 완료 (Local/S3 듀얼 모드) |

---

## 핵심 기능 및 워크플로우

### 1. 사용자 가입 및 인증 플로우

```
+----------+     +----------+     +----------+     +----------+
|  회원가입  |---->| 프로필   |---->| 본인인증  |---->| 서비스   |
|          |     |  생성    |     | (SMS)   |     |  이용    |
+----------+     +----------+     +----------+     +----------+
     |                                                   |
     |              +------------------+                 |
     |              |   사업자 인증     |                 |
     |              | (스튜디오 Only)  |                 |
     |              +------------------+                 |
     |                       |                           |
     +-----------------------+---------------------------+
                             |
                             v
                    +------------------+
                    |   서비스 이용    |
                    | (인증 배지 표시) |
                    +------------------+
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
```

### 2. 구인/구직 매칭 플로우

```
+-----------------------------------------------------------+
|                      스튜디오                                |
+---------------------------+-------------------------------+
                            |
                            v
              +-------------------------+
              |     구인 공고 등록       |
              |  - 카테고리 (필라/요가)  |
              |  - 시급, 시간, 지역      |
              |  - 필요 자격증           |
              +-----------+-------------+
                          |
        +-----------------+-----------------+
        |                 |                 |
        v                 v                 v
   +---------+      +---------+      +---------+
   | 강사 A  |      | 강사 B  |      | 강사 C  |
   | 92% 매칭|      | 78% 매칭|      | 45% 매칭|
   +----+----+      +----+----+      +----+----+
        |                |                |
        +----------------+----------------+
                         |
                         v
              +-------------------------+
              |     매칭 점수 계산       |
              |  지역(30%) + 경력(25%)  |
              |  자격증(25%) + 시급(20%)|
              |  프리미엄: x1.3 부스트  |
              +-------------------------+
```

**매칭 점수 계산 알고리즘:**
```python
def calculate_matching_score(instructor, job, is_premium=False):
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

    # 프리미엄 부스트 (30%)
    if is_premium:
        total = min(total * 1.3, 100)

    return {"total": total, "breakdown": scores}
```

### 3. 계약 상태 머신

```
                    +-----------------+
                    |    CONFIRMED    | <-- 오퍼 수락 시 생성
                    |    (확정됨)     |
                    +--------+--------+
                             |
              +--------------+--------------+
              |                             |
              v                             v
     +-------------+              +-------------+
     |  CANCELLED  |              | IN_PROGRESS |
     |   (취소)    |              |   (진행중)  |
     +-------------+              +------+------+
              ^                          |
              |              +-----------+-----------+
              |              |                       |
              |              v                       v
              |     +-------------+         +-----------------+
              +-----|  CANCELLED  |         |    COMPLETED    |
                    |   (취소)    |         |    (완료)       |
                    +-------------+         |  양쪽 확인 완료  |
                                            +-----------------+
                                                     |
                                                     v
                                        +-----------------------------+
                                        |        노쇼 신고            |
                                        |  - Trust Score 감점         |
                                        |  - 3회 누적 시 계정 정지     |
                                        +-----------------------------+
```

**상태 전이 규칙:**
```python
VALID_TRANSITIONS = {
    ContractStatus.CONFIRMED: {
        ContractStatus.IN_PROGRESS,  # 양쪽 서명 후
        ContractStatus.CANCELLED,    # 취소
    },
    ContractStatus.IN_PROGRESS: {
        ContractStatus.PENDING_COMPLETION,  # 한쪽 완료 확인
        ContractStatus.CANCELLED,    # 취소
    },
    ContractStatus.PENDING_COMPLETION: {
        ContractStatus.COMPLETED,    # 양쪽 완료 확인
        ContractStatus.CANCELLED,    # 취소
    },
    ContractStatus.COMPLETED: set(),   # 최종 상태
    ContractStatus.CANCELLED: set(),   # 최종 상태
}
```

### 4. 노쇼 패널티 시스템

```
              +-------------------------+
              |    노쇼 신고 접수       |
              | POST /contracts/{id}/   |
              |      report-no-show     |
              +-----------+-------------+
                          |
                          v
              +-------------------------+
              |   패널티 자동 적용      |
              | - no_show_count += 1    |
              | - Trust Score 감점      |
              | - 계약 자동 취소        |
              +-----------+-------------+
                          |
           +--------------+--------------+
           |              |              |
           v              v              v
      +---------+   +---------+   +---------+
      | 1회차   |   | 2회차   |   | 3회차   |
      | 경고    |   | 경고    |   | 정지    |
      | 잔여2회 |   | 잔여1회 |   | 계정차단|
      +---------+   +---------+   +---------+
```

---

## 프리미엄 멤버십 시스템

### 요금: 월 9,900원

### 공통 혜택 (강사 + 스튜디오)

| 혜택 | 무료 회원 | 프리미엄 회원 |
|------|----------|-------------|
| 프리미엄 배지 | - | 프로필에 표시 |
| Trust Score 보너스 | - | +10점 |

### 강사 전용 혜택

| 혜택 | 무료 회원 | 프리미엄 회원 |
|------|----------|-------------|
| 일일 지원 횟수 | 5회 | 무제한 |
| 매칭 점수 부스트 | - | x1.3 (30% 부스트) |
| 지원서 템플릿 | - | 최대 10개 저장 |

### 스튜디오 전용 혜택

| 혜택 | 무료 회원 | 프리미엄 회원 |
|------|----------|-------------|
| 강사 프로필 열람 | 5명/일 | 무제한 |
| 공고 노출 순위 | 일반 | 우선 노출 |
| 프리미엄 강사 매칭 | - | 우선 정렬 |

### 일일 사용 제한 시스템

- 데이터베이스: `daily_usage_limits` 테이블
- 리셋 시간: 매일 자정
- 추적 필드: `daily_applications_today`, `daily_views_today`, `last_usage_reset_date`

---

## 데이터베이스 설계

### ERD (Entity Relationship Diagram)

```
+------------------+       +------------------+
|      users       |       |instructor_profiles|
+------------------+       +------------------+
| id (PK)          |--+    | id (PK)          |
| email            |  |    | user_id (FK)-----+--+
| hashed_password  |  |    | display_name     |  |
| role             |  |    | bio              |  |
| is_active        |  |    | certifications   |  |
| phone            |  |    | experience_years |  |
| phone_verified   |  |    | hourly_rate_min  |  |
| identity_verified|  |    | hourly_rate_max  |  |
| business_number  |  |    | available_regions|  |
| business_verified|  |    | rating_average   |  |
| no_show_count    |  |                          |
| is_suspended     |  |    +------------------+  |
+------------------+  |    | studio_profiles  |  |
                      |    +------------------+  |
                      |    | id (PK)          |  |
                      +----| user_id (FK)-----+--+
                           | business_name    |
                           | address          |
                           | region           |
                           | rating_average   |
                           +--------+---------+
                                    |
                           +--------+--------+
                           v                 v
               +------------------+  +------------------+
               |    job_posts     |  |   applications   |
               +------------------+  +------------------+
               | id (PK)          |  | id (PK)          |
               | studio_id (FK)---|  | job_post_id(FK)--|
               | title            |  | instructor_id(FK)|
               | category         |  | status           |
               | job_type         |  | cover_letter     |
               | hourly_rate      |  +--------+---------+
               | date             |           |
               | required_certs   |           v
               | status           |  +------------------+
               +------------------+  |     offers       |
                                     +------------------+
                                     | id (PK)          |
                                     | application_id   |
                                     | studio_id        |
                                     | instructor_id    |
                                     | proposed_rate    |
                                     | status           |
                                     +--------+---------+
                                              |
                                              v
                                     +------------------+
                                     |    contracts     |
                                     +------------------+
                                     | id (PK)          |
                                     | offer_id (FK)    |
                                     | studio_id        |
                                     | instructor_id    |
                                     | status           |--> CONFIRMED
                                     | total_amount     |    IN_PROGRESS
                                     | date             |    COMPLETED
                                     | cancellation_    |    CANCELLED
                                     |   reason         |
                                     +--------+---------+
                                              |
                                              v
                                     +-------------+
                                     |   reviews   |
                                     +-------------+
                                     | id          |
                                     | contract_id |
                                     | rating      |
                                     | comment     |
                                     +-------------+

  +-------------------+  +-------------------+  +-------------------+
  |   subscriptions   |  |   daily_usage     |  |   chat_threads    |
  +-------------------+  +-------------------+  +-------------------+
  | id (PK)           |  | id (PK)           |  | id (PK)           |
  | user_id (FK)      |  | user_id (FK)      |  | participant_1 (FK)|
  | plan              |  | applications_today|  | participant_2 (FK)|
  | status            |  | views_today       |  +-------------------+
  | billing_key       |  | reset_date        |         |
  +-------------------+  +-------------------+         v
                                               +-------------------+
  +-------------------+  +-------------------+ |  chat_messages    |
  |     reports       |  |  support_tickets  | +-------------------+
  +-------------------+  +-------------------+ | id (PK)           |
  | id (PK)           |  | id (PK)           | | thread_id (FK)    |
  | reporter_id (FK)  |  | user_id (FK)      | | sender_id (FK)    |
  | reported_id (FK)  |  | category          | | content           |
  | reason            |  | status            | +-------------------+
  +-------------------+  +-------------------+
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

    -- 패널티
    no_show_count   INTEGER DEFAULT 0,
    is_suspended    BOOLEAN DEFAULT FALSE,

    created_at      TIMESTAMP NOT NULL,
    updated_at      TIMESTAMP NOT NULL
);
```

### DB 호환성 규칙

| 문제 | 해결책 |
|------|--------|
| UUID 타입 | `GUID` 커스텀 타입 (CHAR(36)) |
| Enum 타입 | `String(20)` 사용 |
| Array 타입 | `JSON` 사용 |

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
    "items": [],
    "total": 100,
    "page": 1,
    "page_size": 20
}
```

### 전체 API 엔드포인트

#### 인증 (Auth)
| Method | Endpoint | 설명 | 인증 |
|--------|----------|------|------|
| POST | `/auth/signup` | 회원가입 | - |
| POST | `/auth/login` | 로그인 (JWT 발급) | - |
| POST | `/auth/refresh` | 토큰 갱신 | Refresh Token |
| GET | `/auth/me` | 내 정보 조회 | Bearer |
| POST | `/auth/logout` | 로그아웃 (토큰 무효화) | Bearer |
| POST | `/auth/password-reset/request` | 비밀번호 재설정 요청 | - |
| POST | `/auth/password-reset/confirm` | 비밀번호 재설정 확인 | - |

#### 본인/사업자 인증 (Verification)
| Method | Endpoint | 설명 | 인증 |
|--------|----------|------|------|
| POST | `/verification/phone/request` | SMS OTP 요청 | Bearer |
| POST | `/verification/phone/verify` | OTP 검증 | Bearer |
| POST | `/verification/business/verify` | 사업자등록번호 인증 | Bearer |
| GET | `/verification/status` | 인증 상태 조회 | Bearer |

#### 구독 (Subscription)
| Method | Endpoint | 설명 | 인증 |
|--------|----------|------|------|
| GET | `/subscriptions/status` | 구독 상태 조회 | Bearer |
| POST | `/subscriptions/upgrade` | 프리미엄 업그레이드 | Bearer |
| POST | `/subscriptions/cancel` | 구독 취소 | Bearer |
| POST | `/subscriptions/billing-key` | 빌링키 등록 | Bearer |

#### Trust Score
| Method | Endpoint | 설명 | 인증 |
|--------|----------|------|------|
| GET | `/trust-score` | Trust Score 조회 | Bearer |
| GET | `/trust-score/display` | 표시용 Trust Score | Bearer |

#### 프로필 (Profiles)
| Method | Endpoint | 설명 | 인증 |
|--------|----------|------|------|
| GET | `/profiles/me` | 내 프로필 조회 | Bearer |
| PUT | `/profiles/me` | 프로필 수정 | Bearer |

#### 강사 (Instructors)
| Method | Endpoint | 설명 | 인증 |
|--------|----------|------|------|
| GET | `/instructors/{id}` | 강사 프로필 상세 | Bearer (열람 추적) |

#### 스튜디오 (Studios)
| Method | Endpoint | 설명 | 인증 |
|--------|----------|------|------|
| GET | `/studios/{id}` | 스튜디오 프로필 상세 | Bearer |

#### 공고 (Job Posts)
| Method | Endpoint | 설명 | 인증 |
|--------|----------|------|------|
| GET | `/job-posts` | 공고 목록 (필터링) | Bearer |
| GET | `/job-posts/for-me/with-matching` | 매칭 점수 포함 목록 | Bearer (강사) |
| POST | `/job-posts` | 공고 등록 | Bearer (스튜디오) |
| GET | `/job-posts/{id}` | 공고 상세 | Bearer |

#### 지원서 (Applications)
| Method | Endpoint | 설명 | 인증 |
|--------|----------|------|------|
| POST | `/applications` | 지원서 제출 (일일 제한 적용) | Bearer (강사) |
| GET | `/applications/me` | 내 지원 목록 | Bearer |

#### 오퍼 (Offers)
| Method | Endpoint | 설명 | 인증 |
|--------|----------|------|------|
| POST | `/offers` | 오퍼 전송 | Bearer (스튜디오) |
| POST | `/offers/{id}/accept` | 오퍼 수락 | Bearer (강사) |
| POST | `/offers/{id}/reject` | 오퍼 거절 | Bearer (강사) |

#### 계약 (Contracts)
| Method | Endpoint | 설명 | 인증 |
|--------|----------|------|------|
| POST | `/contracts/from-offer/{offer_id}` | 계약 생성 | Bearer |
| GET | `/contracts/me` | 내 계약 목록 | Bearer |
| POST | `/contracts/{id}/set-in-progress` | 진행 시작 | Bearer |
| POST | `/contracts/{id}/complete` | 완료 처리 | Bearer |
| POST | `/contracts/{id}/cancel` | 취소 | Bearer |
| POST | `/contracts/{id}/report-no-show` | 노쇼 신고 | Bearer |

#### 채팅 (Chat)
| Method | Endpoint | 설명 | 인증 |
|--------|----------|------|------|
| POST | `/threads` | 채팅방 생성 | Bearer |
| GET | `/threads` | 채팅방 목록 | Bearer |
| GET | `/threads/{id}/messages` | 메시지 목록 | Bearer |
| POST | `/threads/{id}/messages` | 메시지 전송 | Bearer |
| WS | `/chat/ws/threads/{id}` | WebSocket 실시간 연결 | Token |

#### 리뷰 (Reviews)
| Method | Endpoint | 설명 | 인증 |
|--------|----------|------|------|
| POST | `/reviews` | 리뷰 작성 | Bearer |
| GET | `/reviews/{user_id}` | 사용자 리뷰 조회 | Bearer |

#### 신고/차단 (Reports)
| Method | Endpoint | 설명 | 인증 |
|--------|----------|------|------|
| POST | `/reports` | 신고 접수 | Bearer |
| POST | `/reports/block/{user_id}` | 사용자 차단 | Bearer |

#### 고객지원 (Support)
| Method | Endpoint | 설명 | 인증 |
|--------|----------|------|------|
| POST | `/support/tickets` | 문의 접수 | Bearer |
| GET | `/support/tickets/me` | 내 문의 목록 | Bearer |

#### 일일 사용량 (Usage)
| Method | Endpoint | 설명 | 인증 |
|--------|----------|------|------|
| GET | `/usage/status` | 일일 사용량 조회 | Bearer |

#### 알림 (Notifications)
| Method | Endpoint | 설명 | 인증 |
|--------|----------|------|------|
| GET | `/notifications` | 알림 목록 | Bearer |
| POST | `/notifications/{id}/read` | 알림 읽음 처리 | Bearer |

#### 지원서 템플릿 (Templates) - Premium Only
| Method | Endpoint | 설명 | 인증 |
|--------|----------|------|------|
| GET | `/templates` | 템플릿 목록 | Bearer (프리미엄) |
| POST | `/templates` | 템플릿 생성 | Bearer (프리미엄) |
| DELETE | `/templates/{id}` | 템플릿 삭제 | Bearer (프리미엄) |

---

## 보안 및 인증

### JWT 인증 체계

```
+----------+                    +----------+                    +----------+
|  Client  |                    |  Server  |                    |    DB    |
+----+-----+                    +----+-----+                    +----+-----+
     |                               |                               |
     |  POST /auth/login             |                               |
     |  {email, password}            |                               |
     |------------------------------>|                               |
     |                               |   SELECT user WHERE email    |
     |                               |------------------------------>|
     |                               |                               |
     |                               |   user data                   |
     |                               |<------------------------------|
     |                               |                               |
     |                               |  bcrypt.verify(password)      |
     |                               |  jose.jwt.encode({sub: id})   |
     |                               |                               |
     |  {access_token, refresh_token}|                               |
     |  Set-Cookie: httpOnly         |                               |
     |<------------------------------|                               |
     |                               |                               |
     |  GET /auth/me                 |                               |
     |  Cookie: httpOnly token       |                               |
     |------------------------------>|                               |
     |                               |   jwt.decode(token)           |
     |                               |   SELECT user WHERE id        |
     |                               |------------------------------>|
     |                               |<------------------------------|
     |  {user data}                  |                               |
     |<------------------------------|                               |
```

### 보안 기능 요약

| 보안 영역 | 구현 방식 |
|-----------|----------|
| **인증** | JWT Access + Refresh Token, httpOnly Cookie (BFF 패턴) |
| **암호화** | bcrypt (passlib) + salt 자동 생성 |
| **토큰 관리** | 토큰 블랙리스트 (로그아웃 시 무효화) |
| **Rate Limiting** | slowapi (100 req/min 기본값) |
| **보안 헤더** | X-Frame-Options, CSP, X-XSS-Protection |
| **웹훅 검증** | HMAC-SHA256 서명 검증 (구독 웹훅) |
| **CORS** | 허용된 origin만 접근 |
| **입력 검증** | Pydantic + Zod 이중 검증 |

### 권한 체크

```python
# 역할 기반 접근 제어
@router.post("/job-posts")
async def create_job_post(
    current_user: User = Depends(require_role(UserRole.STUDIO))  # 스튜디오만
):
    ...

# 일반 인증
@router.get("/auth/me")
async def get_me(
    current_user: User = Depends(get_current_user)  # 모든 인증 사용자
):
    ...
```

---

## 설치 및 실행

### 사전 요구사항

- Docker & Docker Compose
- Python 3.11+ (로컬 개발 시)
- Node.js 20+ (프론트엔드 로컬 개발 시)
- uv (Python 패키지 매니저)
- pnpm (Node 패키지 매니저)

### Docker 실행 (권장)

```bash
# 1. 저장소 클론
git clone https://github.com/your-repo/PilaMatch.git
cd PilaMatch

# 2. 환경변수 설정
cp .env.example .env
# .env 파일 수정 (아래 환경 변수 섹션 참고)

# 3. 서비스 시작 (db, redis, backend, frontend)
docker-compose up -d --build

# 4. 로그 확인
docker-compose logs -f backend

# 5. 접속
# API 문서: http://localhost:8000/api/v1/docs
# Frontend: http://localhost:3000

# 6. 데이터베이스 초기화 (주의: 모든 데이터 삭제)
docker-compose down -v && docker-compose up -d
```

### 로컬 개발

```bash
# Backend
cd backend
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000

# Frontend (새 터미널)
cd frontend-next
pnpm install
pnpm dev
# http://localhost:3000 에서 확인
```

### Docker Compose 서비스

| 서비스 | 이미지 | 포트 | 설명 |
|--------|--------|------|------|
| `db` | postgres:15-alpine | 5432 | PostgreSQL 데이터베이스 |
| `redis` | redis:7-alpine | 6379 | OTP 캐싱, 세션 (AOF, 256MB LRU) |
| `backend` | Custom (Dockerfile) | 8000 | FastAPI 백엔드 |
| `frontend` | Custom (3-stage) | 3000 | Next.js 프론트엔드 |

### 환경 변수

```bash
# === Database ===
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/pilamatch
DATABASE_URL_SYNC=postgresql://postgres:password@localhost:5432/pilamatch
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your-password
POSTGRES_DB=pilamatch

# === Security ===
SECRET_KEY=your-super-secret-key-change-in-production
DEBUG=false
APP_ENV=production

# === Redis ===
REDIS_URL=redis://redis:6379/0

# === TossPayments (구독 결제 전용) ===
TOSS_CLIENT_KEY=test_ck_...
TOSS_SECRET_KEY=test_sk_...
TOSS_WEBHOOK_SECRET=your-webhook-secret

# === SMS (Solapi) ===
SMS_PROVIDER=mock          # mock | coolsms | solapi
SMS_API_KEY=your-api-key
SMS_API_SECRET=your-api-secret
SMS_SENDER_NUMBER=01012345678

# === 국세청 API ===
NTS_SERVICE_KEY=your-service-key

# === Storage ===
STORAGE_BACKEND=local      # local | s3
# S3 설정 (STORAGE_BACKEND=s3 일 때)
# AWS_ACCESS_KEY_ID=...
# AWS_SECRET_ACCESS_KEY=...
# AWS_S3_BUCKET_NAME=...
# AWS_S3_REGION=ap-northeast-2

# === Frontend (빌드 타임) ===
NEXT_PUBLIC_API_URL=http://localhost:3000/api/v1
NEXT_PUBLIC_TOSS_CLIENT_KEY=test_ck_...
NEXT_PUBLIC_KAKAO_MAP_KEY=your-kakao-key
FRONTEND_URL=http://localhost:3000

# === Cron ===
CRON_SECRET=your-cron-secret
```

---

## 테스트

### Backend (pytest)

```bash
cd backend

# 전체 테스트
uv run pytest

# 커버리지 포함
uv run pytest --cov=app --cov-report=html

# 특정 테스트 파일
uv run pytest tests/test_auth.py -v

# 계약/패널티 관련 테스트
uv run pytest tests/test_contract*.py -v
```

### Frontend (Vitest)

```bash
cd frontend-next

# 테스트 실행
pnpm test

# Watch 모드
pnpm test:watch
```

### E2E (Playwright)

```bash
uv add --dev pytest-playwright
uv run playwright install chromium
uv run pytest tests/e2e/ -v
```

### CI/CD Pipeline (GitHub Actions)

```
lint (ruff) --> test (pytest + coverage) --> build (docker compose)
```

- Push/PR to `main`, `feat/*` 브랜치에서 자동 실행
- PostgreSQL 15 서비스 컨테이너로 통합 테스트
- Codecov 커버리지 리포트 업로드

### 테스트 우선순위

```
P0 (반드시 테스트):
  - 회원가입/로그인 인증 플로우
  - 계약 상태 전이 (state machine)
  - 양쪽 완료 확인 플로우
  - 노쇼 패널티 -> 3회 정지

P1 (기능 완성 시 테스트):
  - 매칭 알고리즘 점수 계산
  - 프리미엄 멤버십 혜택 적용
  - 일일 사용량 제한/리셋

P2 (시간 여유 시):
  - 프로필 CRUD
  - 공고 목록 정렬/필터
  - 리뷰 작성
```

---

## 개발 가이드

### 코드 컨벤션

- **Python**: PEP 8, ruff linter
- **TypeScript**: ESLint + Prettier
- **Type Hints**: 모든 함수에 타입 힌트 필수
- **Docstrings**: Google style
- **Async/await**: 모든 I/O 작업에 적용

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

### 주요 개발 태스크

#### 새 API 엔드포인트 추가

1. `backend/app/api/v1/endpoints/` 에 라우터 생성
2. `backend/app/services/` 에 서비스 추가
3. `backend/app/schemas/` 에 스키마 생성
4. `backend/app/api/v1/router.py` 에 라우터 등록
5. `backend/tests/` 에 테스트 작성

#### DB 스키마 변경

1. `backend/app/models/` 에서 모델 수정
2. 마이그레이션 생성: `alembic revision --autogenerate -m "description"`
3. 마이그레이션 파일 리뷰
4. 적용: `alembic upgrade head`

---

## 다이어그램 (Mermaid)

> GitHub, GitLab, Notion 등에서 자동 렌더링됩니다.

### 시스템 아키텍처

```mermaid
flowchart TB
    subgraph Client["Client Layer"]
        Web["Next.js<br/>(Web App)"]
        Mobile["Mobile App<br/>(Future)"]
    end

    subgraph API["API Layer"]
        BFF["BFF (Next.js API Routes)"]
        subgraph FastAPI["FastAPI Backend"]
            Auth["Auth<br/>Service"]
            Jobs["Jobs<br/>Service"]
            Contract["Contract<br/>Service"]
            Matching["Matching<br/>Service"]
            Chat["Chat<br/>Service"]
            Trust["Trust Score<br/>Service"]
            Sub["Subscription<br/>Service"]
        end
    end

    subgraph Data["Data Layer"]
        PostgreSQL[(PostgreSQL 15)]
        Redis[(Redis 7<br/>OTP Cache)]
        S3[(S3 / Local<br/>Storage)]
    end

    subgraph External["External Services"]
        Toss["TossPayments"]
        SMS["Solapi<br/>(CoolSMS v4)"]
        NTS["국세청 API"]
    end

    Web & Mobile --> BFF
    BFF --> FastAPI
    Auth & Jobs & Contract & Matching & Chat & Trust & Sub --> PostgreSQL
    Auth --> Redis
    Sub --> Toss
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
    E --> F[사업자인증<br/>국세청 API]
    D --> G[서비스 이용<br/>인증 배지 표시]
    F --> G
    G --> I{프리미엄?}
    I -->|구독| J[프리미엄 혜택<br/>월 9,900원]
    I -->|무료| K[기본 사용<br/>일일 제한 적용]
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

    CONFIRMED --> IN_PROGRESS: 양쪽 서명
    CONFIRMED --> CANCELLED: 취소 요청

    IN_PROGRESS --> COMPLETED: 수업 완료
    IN_PROGRESS --> CANCELLED: 취소/노쇼

    COMPLETED --> [*]
    CANCELLED --> [*]

    note right of COMPLETED
        양쪽 완료 확인 완료
        수업료는 직접 정산
    end note
```

### 노쇼 패널티 시스템

```mermaid
flowchart TD
    A[노쇼 신고 접수] --> B[패널티 적용]
    B --> C{no_show_count}

    C -->|1회| D[경고<br/>Trust Score 감점<br/>잔여 2회]
    C -->|2회| E[경고<br/>Trust Score 감점<br/>잔여 1회]
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
    users ||--o| subscriptions : subscribes
    users ||--o| daily_usage_limits : tracks

    studio_profiles ||--o{ job_posts : creates
    job_posts ||--o{ applications : receives
    instructor_profiles ||--o{ applications : submits

    applications ||--o| offers : generates
    offers ||--o| contracts : creates

    contracts ||--o{ reviews : has
    contracts ||--o{ contract_event_logs : logs

    users ||--o{ chat_threads : participates
    chat_threads ||--o{ chat_messages : contains

    users ||--o{ reports : reports
    users ||--o{ notifications : receives

    users {
        uuid id PK
        string email UK
        string role
        boolean phone_verified
        boolean business_verified
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

    subscriptions {
        uuid id PK
        uuid user_id FK
        string plan
        string status
        string billing_key
    }
```

### 전체 서비스 플로우

```mermaid
flowchart TB
    subgraph Registration["1. 가입/인증"]
        R1[회원가입] --> R2[본인인증]
    end

    subgraph Matching["2. 매칭"]
        M1[공고 등록] --> M2[매칭 점수 계산]
        M2 --> M3[지원서 제출]
        M3 --> M4[오퍼 전송]
        M4 --> M5[오퍼 수락]
    end

    subgraph Contract["3. 계약"]
        C1[계약 생성] --> C2[양쪽 서명]
        C2 --> C3[수업 진행]
        C3 --> C4{결과}
        C4 -->|완료| C5[완료 확인]
        C4 -->|취소| C6[계약 취소]
        C4 -->|노쇼| C7[패널티 적용]
    end

    subgraph Review["4. 리뷰"]
        V1[리뷰 작성] --> V2[평점 갱신]
        V2 --> V3[Trust Score 반영]
    end

    Registration --> Matching
    Matching --> Contract
    Contract --> Review
```

---

## Production Checklist

- [ ] `SECRET_KEY` 변경 (강력한 랜덤 문자열)
- [ ] `DEBUG=false` 설정
- [ ] `APP_ENV=production` 설정
- [ ] `SMS_PROVIDER=solapi` + API 키 설정
- [ ] TossPayments live 키 설정
- [ ] `TOSS_WEBHOOK_SECRET` 설정
- [ ] CORS 설정 검토 (허용된 origin만)
- [ ] Rate Limiting 설정 확인
- [ ] PostgreSQL 백업 전략 수립
- [ ] Redis persistence 설정
- [ ] 모니터링 설정 (Sentry 등)
- [ ] SSL/TLS 인증서 설정
- [ ] 보안 헤더 확인

---

## 라이선스

Private - All rights reserved

---

## 문의

- 개발 문서: [CLAUDE.md](./CLAUDE.md)
- 세션 기록: [docs/](./docs/)
- API 문서 (로컬): http://localhost:8000/api/v1/docs

---

*Last updated: 2026-03-01*
