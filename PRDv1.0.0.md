# Product Requirements Document (PRD)
# PilaMatch - 필라테스/요가 강사 매칭 플랫폼

**Version**: 1.0.0
**작성일**: 2026-02-14
**상태**: MVP 구현 완료

---

## 목차

1. [Executive Summary](#1-executive-summary)
2. [문제 정의 및 시장 분석](#2-문제-정의-및-시장-분석)
3. [솔루션 개요](#3-솔루션-개요)
4. [비즈니스 목표](#4-비즈니스-목표)
5. [타겟 사용자](#5-타겟-사용자)
6. [핵심 기능 요구사항](#6-핵심-기능-요구사항)
7. [비기능 요구사항](#7-비기능-요구사항)
8. [기술 아키텍처](#8-기술-아키텍처)
9. [데이터베이스 설계](#9-데이터베이스-설계)
10. [API 설계](#10-api-설계)
11. [보안 요구사항](#11-보안-요구사항)
12. [성능 요구사항](#12-성능-요구사항)
13. [UI/UX 요구사항](#13-uiux-요구사항)
14. [배포 및 운영](#14-배포-및-운영)
15. [성공 지표](#15-성공-지표)
16. [로드맵](#16-로드맵)

---

## 1. Executive Summary

### 1.1 제품 비전
> "작지만 믿을 수 있는 플랫폼" - 신뢰 기반의 필라테스/요가 강사-스튜디오 매칭 서비스

### 1.2 핵심 가치
- **신뢰 (Trust)**: 검증된 사용자, 안전한 거래, 투명한 시스템
- **간단함 (Simplicity)**: 핵심 기능에 집중, 직관적인 UX
- **안정성 (Stability)**: 서비스 가용성 99.9% 이상 목표

### 1.3 제품 개요
PilaMatch는 필라테스/요가 강사와 스튜디오를 연결하는 B2B 매칭 플랫폼으로, 검증된 사용자 간의 안전한 거래를 보장하는 신뢰 기반 서비스입니다.

---

## 2. 문제 정의 및 시장 분석

### 2.1 시장 문제점

#### 기존 서비스(호호요가 등)의 문제점
| 문제 영역 | 구체적 문제 | 영향 |
|----------|------------|------|
| **기술적 불안정성** | 잦은 앱 크래시, 하얀 화면 버그 | 사용자 이탈률 증가 |
| **신뢰 부재** | 가짜 프로필, 무자격 강사 | 거래 분쟁 발생 |
| **노쇼 문제** | 무단 결석 빈번, 패널티 부재 | 스튜디오 운영 손실 |
| **복잡한 UI** | 불필요한 기능 과다 | 학습 곡선 증가 |
| **결제 불안** | 직접 송금으로 인한 사기 위험 | 금전적 손실 |

### 2.2 시장 규모
- **국내 필라테스 시장**: 약 2조원 규모 (2024년 기준)
- **등록 스튜디오**: 약 15,000개
- **활동 강사**: 약 50,000명
- **연평균 성장률**: 15%

### 2.3 경쟁 분석
| 경쟁사 | 장점 | 단점 | 차별화 포인트 |
|--------|------|------|--------------|
| 호호요가 | 시장 선점 | 기술적 불안정, 검증 부재 | 안정성, 신뢰 시스템 |
| 직접 구인구직 | 수수료 없음 | 번거로움, 위험성 | 자동 매칭, 안전 거래 |
| 인력 소개소 | 오프라인 신뢰 | 높은 수수료(20-30%) | 낮은 수수료(5%) |

---

## 3. 솔루션 개요

### 3.1 핵심 솔루션

#### 신뢰 시스템 (Trust System)
```
┌─────────────────────────────────────────┐
│           4-Layer Trust System          │
├─────────────────────────────────────────┤
│ 1. Identity Verification (본인인증)     │
│    - SMS OTP (6자리)                    │
│    - 사업자등록번호 검증                 │
├─────────────────────────────────────────┤
│ 2. Deposit System (보증금)              │
│    - 기본 50,000원 예치                  │
│    - 노쇼 시 30,000원 차감              │
├─────────────────────────────────────────┤
│ 3. Escrow Payment (에스크로)            │
│    - 플랫폼 보관 → 완료 후 지급          │
│    - 자동 환불/정산 시스템               │
├─────────────────────────────────────────┤
│ 4. Penalty System (패널티)              │
│    - 노쇼 3회 계정 정지                  │
│    - 신고/차단 시스템                    │
└─────────────────────────────────────────┘
```

### 3.2 매칭 알고리즘
4개 요소 가중치 기반 점수 계산 (0-100점):
- **지역 적합도**: 30% - 활동 가능 지역 매칭
- **경력 충족도**: 25% - 요구 경력 대비 실제 경력
- **자격증 보유**: 25% - 필수 자격증 매칭률
- **희망 시급**: 20% - 시급 범위 적합도

### 3.3 제공 가치
| 대상 | 제공 가치 |
|------|----------|
| **스튜디오** | 검증된 강사 풀, 노쇼 보장, 간편한 관리 |
| **강사** | 안정적인 일자리, 빠른 정산, 공정한 평가 |
| **플랫폼** | 거래 수수료 5%, 데이터 기반 매칭 개선 |

---

## 4. 비즈니스 목표

### 4.1 단기 목표 (6개월)
- **사용자 획득**: 스튜디오 500개, 강사 2,000명
- **거래 활성화**: 월간 거래 1,000건
- **서비스 안정화**: 가용성 99.9% 달성

### 4.2 중기 목표 (1년)
- **시장 점유율**: 서울/경기 10% 점유
- **매출 목표**: 월 매출 5,000만원
- **브랜드 인지도**: 업계 Top 3 진입

### 4.3 장기 목표 (2년)
- **전국 확장**: 7대 광역시 진출
- **서비스 확장**: 개인 레슨, 그룹 클래스 추가
- **플랫폼화**: 강사 교육, 자격증 인증 서비스

### 4.4 수익 모델
| 수익원 | 내용 | 비율/금액 |
|--------|------|----------|
| **거래 수수료** | 계약 완료 시 수수료 | 거래액의 5% |
| **프리미엄 멤버십** | 우선 노출, 무제한 지원 | 월 29,900원 |
| **부가 서비스** | 긴급 매칭, 프로필 인증 | 건당 과금 |

---

## 5. 타겟 사용자

### 5.1 Primary Users

#### 스튜디오 운영자
- **Demographics**: 30-40대, 소규모 사업자
- **Pain Points**: 강사 구인 어려움, 노쇼 손실, 관리 부담
- **Needs**: 신뢰할 수 있는 강사, 간편한 관리, 비용 효율성

#### 프리랜서 강사
- **Demographics**: 20-30대, 자격증 보유자
- **Pain Points**: 일자리 찾기 어려움, 불안정한 수입
- **Needs**: 안정적인 일자리, 빠른 정산, 공정한 대우

### 5.2 User Personas

#### Persona 1: 김스튜디오 (35세, 스튜디오 대표)
```
"대체 강사를 급하게 구해야 하는데 믿을 만한 사람을 찾기가 너무 어려워요"
- 서울 강남 소재 필라테스 스튜디오 운영
- 정규 강사 3명, 회원 200명
- 월 1-2회 대체 강사 필요
- 기술에 익숙하지 않음
```

#### Persona 2: 이필라 (28세, 프리랜서 강사)
```
"자격증은 있는데 경력이 부족해서 좋은 스튜디오와 계약하기 어려워요"
- 필라테스 자격증 3개 보유
- 경력 2년, 프리랜서 활동
- 월 수입 목표 300만원
- 다양한 스튜디오 경험 희망
```

---

## 6. 핵심 기능 요구사항

### 6.1 사용자 관리

#### 6.1.1 회원가입/로그인
- **가입 유형**: 강사, 스튜디오 구분
- **인증 방식**: JWT 토큰 기반
- **필수 정보**: 이메일, 비밀번호, 역할, 이름
- **보안**: bcrypt 해싱, refresh token

#### 6.1.2 본인인증
```
강사 인증 프로세스:
1. 휴대폰 번호 입력
2. SMS OTP 발송 (6자리)
3. OTP 검증
4. identity_verified = true

스튜디오 인증 프로세스:
1. 휴대폰 인증 (위와 동일)
2. 사업자등록번호 입력
3. 국세청 API 검증
4. business_verified = true
```

#### 6.1.3 보증금 시스템
- **기본 보증금**: 50,000원
- **충전 방법**: TossPayments 결제
- **차감 규칙**: 노쇼 시 30,000원
- **환불 조건**: 서비스 탈퇴 시, 패널티 없을 때

### 6.2 프로필 관리

#### 6.2.1 강사 프로필
```json
{
  "display_name": "김필라",
  "bio": "10년 경력 필라테스 전문강사",
  "profile_image": "url",
  "categories": ["pilates", "yoga"],
  "experience_years": 10,
  "hourly_rate_min": 50000,
  "hourly_rate_max": 100000,
  "available_regions": ["서울 강남", "서울 서초"],
  "certifications": [
    {
      "name": "BASI Pilates",
      "issuer": "BASI",
      "issue_year": 2020,
      "is_verified": true
    }
  ]
}
```

#### 6.2.2 스튜디오 프로필
```json
{
  "business_name": "강남 필라테스",
  "business_number": "123-45-67890",
  "address": "서울시 강남구 역삼동",
  "region": "서울 강남",
  "description": "프리미엄 필라테스 스튜디오",
  "operating_hours": "09:00-21:00",
  "contact_number": "02-1234-5678",
  "facilities": ["주차장", "샤워실", "락커"],
  "equipment_brands": ["Gratz", "Balanced Body"]
}
```

### 6.3 구인구직

#### 6.3.1 구인공고 (Job Post)
```
필수 정보:
- 제목: "주말 대체 필라테스 강사 구합니다"
- 카테고리: pilates/yoga
- 근무 형태: substitute/contract/regular
- 날짜 및 시간: 2026-02-20, 10:00-18:00
- 시급: 80,000원
- 필요 경력: 3년 이상
- 필수 자격증: ["BASI Pilates", "STOTT Pilates"]
- 지역: "서울 강남"
- 총 회차: 4회

공고 상태:
- OPEN: 지원 가능
- CLOSED: 마감
- CANCELLED: 취소
```

#### 6.3.2 매칭 시스템
```python
매칭 점수 = (
    지역_점수 * 0.30 +
    경력_점수 * 0.25 +
    자격증_점수 * 0.25 +
    시급_점수 * 0.20
)

매칭 라벨:
- 90-100점: Perfect Match
- 75-89점: Great Match
- 60-74점: Good Match
- 40-59점: Fair Match
- 0-39점: Low Match
```

#### 6.3.3 지원서 (Application)
- **지원 제한**: 동일 공고 중복 지원 불가
- **커버레터**: 선택사항, 최대 500자
- **자동 첨부**: 강사 프로필 정보
- **상태 관리**: PENDING → ACCEPTED/REJECTED → WITHDRAWN

### 6.4 계약 관리

#### 6.4.1 오퍼 (Offer)
```
오퍼 생성:
1. 스튜디오 → 강사 전송
2. 제안 시급, 상세 조건 포함
3. 유효기간: 72시간

오퍼 응답:
- ACCEPT: 수락 → 계약 생성
- REJECT: 거절
- EXPIRED: 만료
```

#### 6.4.2 계약 상태 머신
```
        [CONFIRMED]
            ├─→ [IN_PROGRESS] (결제 완료)
            │       ├─→ [COMPLETED] (수업 완료)
            │       └─→ [CANCELLED] (취소+환불)
            └─→ [CANCELLED] (취소)
```

#### 6.4.3 계약 이벤트 로그
모든 상태 전환 기록:
- 행위자 (actor_user_id)
- 이전 상태 → 새 상태
- 변경 시각
- 사유 (note)

### 6.5 결제 시스템

#### 6.5.1 에스크로 결제
```
1. 계약 확정
   ↓
2. 스튜디오 결제 (TossPayments)
   ↓
3. 에스크로 HELD (플랫폼 보관)
   ↓
4. 수업 진행
   ↓
5. 완료 확인
   ↓
6. 에스크로 RELEASED
   ↓
7. 강사 정산 (95%, 수수료 5% 제외)
```

#### 6.5.2 환불 정책
| 시점 | 환불 비율 | 조건 |
|------|----------|------|
| 수업 24시간 전 | 100% | 무조건 |
| 수업 24시간 이내 | 70% | 강사 동의 필요 |
| 수업 시작 후 | 0% | 환불 불가 |
| 노쇼 (강사) | 100% + 패널티 | 자동 처리 |

### 6.6 신뢰 시스템

#### 6.6.1 노쇼 패널티
```python
노쇼 신고 시:
1. no_show_count += 1
2. deposit_balance -= 30000
3. if no_show_count >= 3:
   is_suspended = True
4. 계약 자동 취소
5. 스튜디오 전액 환불
```

#### 6.6.2 리뷰 시스템
- **작성 권한**: 계약 완료 후 7일 이내
- **평가 항목**:
  - 전문성 (1-5점)
  - 시간 준수 (1-5점)
  - 커뮤니케이션 (1-5점)
  - 종합 만족도 (1-5점)
- **리뷰 공개**: 양방향 작성 완료 후

#### 6.6.3 신고/차단
- **신고 사유**: 허위 프로필, 부적절한 행동, 노쇼, 기타
- **처리 절차**: 접수 → 검토 → 조치 → 통보
- **차단 효과**: 상호 프로필 비표시, 매칭 제외

### 6.7 커뮤니케이션

#### 6.7.1 실시간 채팅
- **채팅방 생성**: 계약 체결 시 자동
- **참여자**: 강사, 스튜디오
- **메시지 유형**: 텍스트, 시스템 알림
- **실시간 전송**: WebSocket

#### 6.7.2 알림 시스템
| 이벤트 | 수신자 | 알림 방식 |
|--------|--------|----------|
| 새 지원서 | 스튜디오 | 인앱, 이메일 |
| 오퍼 수신 | 강사 | 인앱, SMS |
| 계약 체결 | 양측 | 인앱, 이메일 |
| 수업 리마인더 | 양측 | SMS (D-1) |
| 노쇼 신고 | 피신고자 | 인앱, 이메일, SMS |

---

## 7. 비기능 요구사항

### 7.1 성능 요구사항
| 항목 | 목표 | 측정 방법 |
|------|------|----------|
| 응답 시간 | < 200ms (95 percentile) | APM 모니터링 |
| 동시 사용자 | 10,000명 | 부하 테스트 |
| 처리량 | 1,000 TPS | 부하 테스트 |
| 가용성 | 99.9% | 업타임 모니터링 |

### 7.2 확장성 요구사항
- **수평 확장**: 컨테이너 기반 스케일링
- **데이터베이스**: Read replica, 샤딩 준비
- **캐싱**: Redis 레이어 구성
- **CDN**: 정적 자원 분산

### 7.3 보안 요구사항
- **인증**: JWT + Refresh Token
- **암호화**: TLS 1.3, AES-256
- **개인정보**: GDPR/개인정보보호법 준수
- **결제**: PCI-DSS 준수

### 7.4 사용성 요구사항
- **학습 시간**: 30분 이내 숙달
- **에러율**: < 1%
- **모바일**: 반응형 디자인
- **접근성**: WCAG 2.1 Level AA

---

## 8. 기술 아키텍처

### 8.1 시스템 아키텍처
```
┌─────────────────────────────────────────┐
│            Client Layer                  │
├─────────────────────────────────────────┤
│  Web (Streamlit) │ Mobile │ Admin       │
└────────┬────────────┬────────┬─────────┘
         │            │        │
         └────────────┼────────┘
                      │
┌─────────────────────┼───────────────────┐
│               API Gateway                │
│            (FastAPI + CORS)              │
└─────────────────────┬───────────────────┘
                      │
┌─────────────────────┴───────────────────┐
│           Application Layer              │
├──────────────────────────────────────────┤
│  ┌─────────┐ ┌─────────┐ ┌─────────┐   │
│  │  Auth   │ │Matching │ │Contract │   │
│  │ Service │ │ Service │ │ Service │   │
│  └─────────┘ └─────────┘ └─────────┘   │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐   │
│  │Payment  │ │Penalty  │ │  Chat   │   │
│  │ Service │ │ Service │ │ Service │   │
│  └─────────┘ └─────────┘ └─────────┘   │
└──────────────────┬──────────────────────┘
                   │
┌──────────────────┴──────────────────────┐
│            Data Layer                    │
├──────────────────────────────────────────┤
│  PostgreSQL │ Redis │ S3 │ Elasticsearch│
└──────────────────────────────────────────┘
                   │
┌──────────────────┴──────────────────────┐
│         External Services                │
├──────────────────────────────────────────┤
│ TossPayments │ NHN SMS │ 국세청 API     │
└──────────────────────────────────────────┘
```

### 8.2 기술 스택
| Layer | Technology | Version | Purpose |
|-------|------------|---------|---------|
| **Language** | Python | 3.11+ | 비동기 성능, 타입 힌트 |
| **Backend** | FastAPI | 0.109+ | REST API, WebSocket |
| **ORM** | SQLAlchemy | 2.0+ | 비동기 DB 작업 |
| **Database** | PostgreSQL | 15+ | ACID, JSON 지원 |
| **Cache** | Redis | 7+ | 세션, OTP 저장 |
| **Queue** | Celery | 5+ | 비동기 작업 |
| **Container** | Docker | 24+ | 컨테이너화 |
| **Frontend** | Streamlit | 1.30+ | MVP UI |
| **Monitoring** | Prometheus | - | 메트릭 수집 |

### 8.3 마이크로서비스 구조 (Future)
```
services/
├── auth-service/        # 인증/인가
├── user-service/        # 사용자 관리
├── matching-service/    # 매칭 엔진
├── contract-service/    # 계약 관리
├── payment-service/     # 결제 처리
├── notification-service/# 알림 발송
└── analytics-service/   # 데이터 분석
```

---

## 9. 데이터베이스 설계

### 9.1 주요 테이블

#### users
```sql
CREATE TABLE users (
    id VARCHAR(36) PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role VARCHAR(20) NOT NULL,  -- 'instructor' | 'studio'

    -- Verification
    phone VARCHAR(20),
    phone_verified BOOLEAN DEFAULT FALSE,
    identity_verified BOOLEAN DEFAULT FALSE,
    business_number VARCHAR(20),
    business_verified BOOLEAN DEFAULT FALSE,

    -- Trust System
    deposit_balance NUMERIC(10,2) DEFAULT 0,
    no_show_count INTEGER DEFAULT 0,
    is_suspended BOOLEAN DEFAULT FALSE,

    -- Timestamps
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);
```

#### contracts
```sql
CREATE TABLE contracts (
    id VARCHAR(36) PRIMARY KEY,
    offer_id VARCHAR(36) REFERENCES offers(id),
    studio_id VARCHAR(36) REFERENCES studio_profiles(id),
    instructor_id VARCHAR(36) REFERENCES instructor_profiles(id),

    status VARCHAR(20) NOT NULL,  -- State machine
    date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    hourly_rate NUMERIC(10,2) NOT NULL,
    total_amount NUMERIC(10,2) NOT NULL,

    cancellation_reason TEXT,
    cancelled_by VARCHAR(36),

    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);
```

#### payments
```sql
CREATE TABLE payments (
    id VARCHAR(36) PRIMARY KEY,
    contract_id VARCHAR(36) REFERENCES contracts(id),

    amount NUMERIC(10,2) NOT NULL,
    platform_fee NUMERIC(10,2) DEFAULT 0,
    status VARCHAR(20) NOT NULL,
    escrow_status VARCHAR(20) DEFAULT 'HELD',

    -- TossPayments
    payment_key VARCHAR(200) UNIQUE,
    order_id VARCHAR(200) UNIQUE NOT NULL,

    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);
```

### 9.2 인덱스 전략
```sql
-- 성능 최적화 인덱스
CREATE INDEX idx_job_posts_status_region ON job_posts(status, region);
CREATE INDEX idx_applications_job_instructor ON applications(job_post_id, instructor_id);
CREATE INDEX idx_contracts_status_date ON contracts(status, date);
CREATE INDEX idx_users_role_verified ON users(role, identity_verified);
```

### 9.3 데이터 보관 정책
| 데이터 유형 | 보관 기간 | 처리 방법 |
|------------|----------|----------|
| 활성 계약 | 무제한 | - |
| 완료 계약 | 5년 | 아카이브 |
| 채팅 메시지 | 1년 | 삭제 |
| 로그 데이터 | 3개월 | S3 이동 |
| 삭제된 사용자 | 30일 | 완전 삭제 |

---

## 10. API 설계

### 10.1 API 구조
```
Base URL: https://api.pilamatch.com/api/v1

인증 헤더:
Authorization: Bearer {jwt_token}
```

### 10.2 주요 엔드포인트

#### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /auth/signup | 회원가입 |
| POST | /auth/login | 로그인 |
| GET | /auth/me | 현재 사용자 정보 |
| POST | /auth/refresh | 토큰 갱신 |
| POST | /auth/logout | 로그아웃 |

#### Job Posts
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /job-posts | 공고 목록 (필터링) |
| GET | /job-posts/for-me/with-matching | 매칭 점수 포함 |
| POST | /job-posts | 공고 등록 |
| GET | /job-posts/{id} | 공고 상세 |
| PUT | /job-posts/{id} | 공고 수정 |
| DELETE | /job-posts/{id} | 공고 삭제 |

#### Contracts
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /contracts/from-offer/{id} | 계약 생성 |
| GET | /contracts/me | 내 계약 목록 |
| POST | /contracts/{id}/set-in-progress | 진행 시작 |
| POST | /contracts/{id}/complete | 완료 처리 |
| POST | /contracts/{id}/cancel | 취소 |
| POST | /contracts/{id}/report-no-show | 노쇼 신고 |

### 10.3 응답 형식

#### 성공 응답
```json
{
    "id": "uuid",
    "data": {},
    "message": "Success",
    "timestamp": "2026-02-14T12:00:00Z"
}
```

#### 에러 응답
```json
{
    "detail": {
        "code": "ERROR_CODE",
        "message": "Human readable message",
        "field": "field_name"  // Validation error
    }
}
```

#### 페이지네이션
```json
{
    "items": [...],
    "total": 100,
    "page": 1,
    "page_size": 20,
    "has_next": true,
    "has_prev": false
}
```

### 10.4 에러 코드
| Code | HTTP Status | Description |
|------|------------|-------------|
| UNAUTHORIZED | 401 | 인증 필요 |
| FORBIDDEN | 403 | 권한 부족 |
| NOT_FOUND | 404 | 리소스 없음 |
| ALREADY_EXISTS | 409 | 중복 데이터 |
| VALIDATION_ERROR | 422 | 검증 실패 |
| INSUFFICIENT_DEPOSIT | 400 | 보증금 부족 |
| NO_SHOW_LIMIT | 403 | 노쇼 한도 초과 |

---

## 11. 보안 요구사항

### 11.1 인증 및 권한
- **JWT 토큰**: Access Token (15분), Refresh Token (7일)
- **비밀번호**: bcrypt 해싱, salt rounds 12
- **2FA**: SMS OTP (프로덕션)
- **권한 체계**: RBAC (Role-Based Access Control)

### 11.2 데이터 보호
| 항목 | 보호 방법 |
|------|----------|
| 전송 중 | TLS 1.3 |
| 저장 중 | AES-256 암호화 |
| 개인정보 | 마스킹, 별도 저장 |
| 결제 정보 | 토큰화, PCI-DSS 준수 |

### 11.3 보안 감사
- **접근 로그**: 모든 API 호출 기록
- **변경 로그**: 중요 데이터 변경 이력
- **이상 탐지**: 비정상 패턴 모니터링
- **정기 점검**: 분기별 보안 감사

### 11.4 OWASP Top 10 대응
| 위협 | 대응 방안 |
|------|----------|
| Injection | Prepared statements, 입력 검증 |
| Broken Authentication | JWT, Rate limiting |
| XSS | CSP 헤더, 출력 인코딩 |
| XXE | XML 파서 비활성화 |
| Broken Access Control | 권한 검증 미들웨어 |
| Security Misconfiguration | 환경별 설정 분리 |
| Sensitive Data Exposure | 암호화, HTTPS only |
| Insufficient Logging | 중앙화된 로깅 시스템 |

---

## 12. 성능 요구사항

### 12.1 응답 시간 목표
| 작업 유형 | 목표 시간 | 측정 기준 |
|-----------|----------|-----------|
| 페이지 로드 | < 1초 | P95 |
| API 응답 | < 200ms | P95 |
| 검색 결과 | < 500ms | P95 |
| 매칭 계산 | < 100ms | P95 |
| 결제 처리 | < 3초 | P99 |

### 12.2 처리량 목표
- **동시 접속**: 10,000 사용자
- **API TPS**: 1,000 requests/sec
- **WebSocket**: 5,000 동시 연결
- **일일 거래**: 10,000건

### 12.3 최적화 전략
```
1. Database
   - Connection pooling
   - Query optimization
   - Indexing strategy
   - Read replicas

2. Caching
   - Redis for sessions
   - API response cache
   - Static asset CDN
   - Database query cache

3. Async Processing
   - Background jobs (Celery)
   - Event-driven architecture
   - Message queue (RabbitMQ)

4. Code Optimization
   - Async/await everywhere
   - Lazy loading
   - Batch processing
   - Resource pooling
```

---

## 13. UI/UX 요구사항

### 13.1 디자인 원칙
- **Simple**: 최소한의 클릭으로 목적 달성
- **Clear**: 명확한 정보 계층구조
- **Consistent**: 일관된 디자인 패턴
- **Responsive**: 모바일 우선 설계

### 13.2 주요 화면

#### 13.2.1 대시보드
```
┌─────────────────────────────────┐
│         오늘의 일정 (2)         │
├─────────────────────────────────┤
│ 10:00 - 강남점 필라테스 수업    │
│ 14:00 - 서초점 요가 수업        │
├─────────────────────────────────┤
│         새로운 매칭 (5)         │
├─────────────────────────────────┤
│ [92%] 주말 대체 강사           │
│ [85%] 평일 오전 강사           │
└─────────────────────────────────┘
```

#### 13.2.2 매칭 리스트
```
┌─────────────────────────────────┐
│   📍 서울 강남 | 💰 80,000원    │
│   주말 필라테스 강사 구합니다   │
│   [Perfect Match 95%]          │
│   📅 2026-02-20 | ⏰ 10:00-18:00│
│   [지원하기]                   │
├─────────────────────────────────┤
│   📍 서울 서초 | 💰 70,000원    │
│   평일 요가 강사 구합니다       │
│   [Great Match 82%]            │
│   📅 2026-02-21 | ⏰ 09:00-12:00│
│   [지원하기]                   │
└─────────────────────────────────┘
```

### 13.3 모바일 UI 가이드라인
- **터치 타겟**: 최소 44x44 px
- **폰트 크기**: 본문 16px 이상
- **컬러 대비**: WCAG AA 기준
- **제스처**: 스와이프, 풀 투 리프레시

### 13.4 접근성
- **스크린 리더**: 모든 요소 라벨링
- **키보드 네비게이션**: Tab 순서 지정
- **색맹 대응**: 색상만으로 구분 금지
- **다국어**: 한국어, 영어 지원

---

## 14. 배포 및 운영

### 14.1 환경 구성
| Environment | Purpose | URL |
|-------------|---------|-----|
| Development | 개발 | dev.pilamatch.com |
| Staging | 테스트 | staging.pilamatch.com |
| Production | 운영 | pilamatch.com |

### 14.2 배포 전략
```yaml
# CI/CD Pipeline
1. Code Commit
   └─→ 2. Run Tests
       └─→ 3. Build Docker Image
           └─→ 4. Push to Registry
               └─→ 5. Deploy to K8s
                   └─→ 6. Health Check
                       └─→ 7. Traffic Switch
```

### 14.3 모니터링
| 도구 | 용도 | 메트릭 |
|------|------|--------|
| Prometheus | 메트릭 수집 | CPU, Memory, Requests |
| Grafana | 시각화 | 대시보드 |
| ELK Stack | 로그 분석 | 에러율, 패턴 |
| Sentry | 에러 추적 | Exception, Stack trace |
| Datadog | APM | Transaction, Trace |

### 14.4 백업 및 복구
- **데이터베이스**: 일일 전체 백업, 시간별 증분 백업
- **파일 스토리지**: S3 versioning
- **복구 목표**: RTO 1시간, RPO 1시간
- **재해 복구**: Multi-region 구성

### 14.5 운영 체크리스트
```
Daily:
□ 서비스 가용성 확인
□ 에러율 모니터링
□ 신규 가입자 확인
□ 거래 현황 확인

Weekly:
□ 성능 메트릭 리뷰
□ 보안 로그 검토
□ 백업 상태 확인
□ 용량 계획 검토

Monthly:
□ 보안 패치 적용
□ 의존성 업데이트
□ 비용 최적화
□ 사용자 피드백 분석
```

---

## 15. 성공 지표

### 15.1 비즈니스 KPI
| 지표 | 목표 (6개월) | 측정 방법 |
|------|------------|-----------|
| MAU | 5,000명 | Google Analytics |
| 거래 전환율 | 30% | 지원→계약 비율 |
| 월 거래액 | 1억원 | 결제 시스템 |
| 재사용률 | 60% | 코호트 분석 |
| NPS | 50+ | 설문조사 |

### 15.2 기술 지표
| 지표 | 목표 | 현재 |
|------|------|------|
| 가용성 | 99.9% | 99.5% |
| 평균 응답시간 | < 200ms | 180ms |
| 에러율 | < 0.1% | 0.15% |
| 테스트 커버리지 | > 80% | 72% |

### 15.3 사용자 만족도
- **앱 평점**: 4.5/5.0 이상
- **리뷰 응답률**: 100%
- **CS 응답시간**: 1시간 이내
- **이탈률**: < 20%

---

## 16. 로드맵

### 16.1 Phase 1: MVP (현재)
**기간**: 2026.01 - 2026.02 ✅
- [x] 핵심 기능 구현
- [x] 신뢰 시스템 구축
- [x] 결제 시스템 연동
- [x] 기본 UI 개발

### 16.2 Phase 2: Growth
**기간**: 2026.03 - 2026.06
- [ ] 모바일 앱 출시 (React Native)
- [ ] 실시간 알림 시스템
- [ ] 프리미엄 멤버십
- [ ] A/B 테스팅 도입

### 16.3 Phase 3: Scale
**기간**: 2026.07 - 2026.12
- [ ] 지역 확장 (7대 광역시)
- [ ] AI 매칭 고도화
- [ ] 강사 교육 프로그램
- [ ] B2B 엔터프라이즈

### 16.4 Phase 4: Platform
**기간**: 2027.01 - 2027.06
- [ ] 오픈 API 제공
- [ ] 써드파티 연동
- [ ] 국제화 (일본, 동남아)
- [ ] 데이터 분석 서비스

### 16.5 기술 부채 해결
| 항목 | 우선순위 | 예상 일정 |
|------|---------|----------|
| 마이크로서비스 전환 | High | Q2 2026 |
| 테스트 커버리지 개선 | High | Q1 2026 |
| 성능 최적화 | Medium | Q2 2026 |
| 레거시 코드 리팩토링 | Low | Q3 2026 |

---

## 부록

### A. 용어 정의
| 용어 | 정의 |
|------|------|
| 노쇼 (No-show) | 예약 후 무단 불참 |
| 에스크로 (Escrow) | 제3자 예치 결제 |
| 매칭 스코어 | 적합도 점수 (0-100) |
| 오퍼 (Offer) | 스튜디오→강사 제안 |
| 보증금 | 신뢰 담보금 (5만원) |

### B. 참고 문서
- [API Documentation](./API_SPEC.md)
- [Database Schema](./DB_SCHEMA.md)
- [Security Policy](./SECURITY.md)
- [Development Guide](./CLAUDE.md)

### C. 연락처
- Product Owner: product@pilamatch.com
- Tech Lead: tech@pilamatch.com
- Customer Support: support@pilamatch.com

---

*이 문서는 살아있는 문서로, 지속적으로 업데이트됩니다.*

**Last Updated**: 2026-02-14
**Version**: 1.0.0
**Status**: MVP Complete