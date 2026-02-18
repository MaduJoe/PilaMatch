# Product Requirements Document (PRD)
# StudioBridge - 필라테스/요가 강사 매칭 플랫폼

**Version**: 2.1.0
**작성일**: 2026-02-16
**상태**: Premium 멤버십 구현 완료 → 운영 준비

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
14. [운영 설계 (1인 개발자)](#14-운영-설계-1인-개발자)
15. [배포 및 인프라](#15-배포-및-인프라)
16. [성공 지표](#16-성공-지표)
17. [로드맵](#17-로드맵)

---

## 1. Executive Summary

### 1.1 제품 비전
> "작지만 믿을 수 있는 플랫폼" - 신뢰 기반의 필라테스/요가 강사-스튜디오 매칭 서비스

### 1.2 핵심 가치
- **신뢰 (Trust)**: 검증된 사용자, 안전한 거래, 투명한 시스템, 공정한 분쟁 해결
- **간결함 (Simplicity)**: 핵심 기능에 집중, 직관적인 UX, 최소 스텝 원칙
- **정확성 (Accuracy)**: 계약/결제 프로세스의 오류 없는 동작, 정책의 명확한 고지
- **안정성 (Stability)**: 서비스 가용성 99.9% 이상 목표

### 1.3 설계 원칙 (v2.1 개정)

#### 간결성 원칙
하나의 앱 안에서 모든 프로세스를 유저가 간편하게 파악 가능해야 한다.
- UI/UX가 누구에게나 직관적이고 쉬워야 한다
- 화면의 이동이나 움직임을 최소화할 것 (등록, 취소 등 과정이 최소 스텝으로 진행)

#### 정확성 원칙
계약이나 결제 관련 프로세스가 오류 없이 정교하게 동작해야 한다.
- 노쇼 발생 시 책임 소재가 명확하고, 노쇼 강사 또한 불만이 없어야 한다
- 취소/환불 정책에 대해 스튜디오, 강사 모두 명확히 인지할 수 있어야 한다

#### 하이브리드 신뢰 원칙 (v2.1 신규)
사용자가 자신의 상황에 맞는 신뢰 방식을 선택할 수 있다.
- **Free**: 전통적인 보증금 기반 신뢰 (50,000원 보증금)
- **Premium**: 구독 기반 편의성 신뢰 (월 9,900원, 보증금 완전 면제)
- Premium ≠ 더 좋은 강사, Premium = 편의성과 우선권

### 1.4 제품 개요
StudioBridge는 필라테스/요가 강사와 스튜디오를 연결하는 B2B 매칭 플랫폼으로, 하이브리드 신뢰 모델(보증금 또는 구독)을 통해 검증된 사용자 간의 안전한 거래를 보장하는 서비스입니다.

### 1.5 Premium 멤버십 가치 제안 (v2.1 신규)
"보증금 부담 없이, 편리하게" - 월 9,900원으로 시작하는 프리미엄 경험

**핵심 차별화**:
- 베테랑 강사 (Free): 높은 시급으로 보증금 부담 상쇄
- 초보 강사 (Premium): 편의성과 우선 노출로 빠른 시작
- 스튜디오: 우선 노출된 Premium 강사 풀 확보

### 1.6 운영 환경
- **운영 주체**: 1인 개발자 (기획/개발/운영 겸업)
- **핵심 전략**: 시스템 자동화를 극대화하여, 사람은 예외 케이스만 처리
- **의사결정 기준**: 자동으로 해결 가능한 구조인가? → Yes면 시스템에 맡김

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
| **분쟁 미해결** | 문제 발생 시 해결 채널 부재 | 양측 불만 누적 |

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
│         5-Layer Trust System            │
├─────────────────────────────────────────┤
│ 1. Identity Verification (본인인증)     │
│    - SMS OTP (6자리)                    │
│    - 사업자등록번호 검증                 │
│    - 자격증 검증 (사진 업로드 + 확인)   │
├─────────────────────────────────────────┤
│ 2. Deposit System (보증금)              │
│    - 기본 30,000원 예치 (런칭 프로모션)  │
│    - 정상가: 50,000원                   │
│    - 노쇼 시 30,000원 차감              │
├─────────────────────────────────────────┤
│ 3. Escrow Payment (에스크로)            │
│    - 플랫폼 보관 → 양측 완료 확인 후 지급│
│    - 자동 환불/정산 시스템               │
├─────────────────────────────────────────┤
│ 4. Penalty System (패널티)              │
│    - 노쇼 신고 → 24h 이의제기 → 확정    │
│    - 3회 누적 시 계정 정지               │
│    - 신고/차단 시스템                    │
├─────────────────────────────────────────┤
│ 5. Trust Score (신뢰 점수)              │
│    - 인증/보증금/노쇼/리뷰/거래 기반     │
│    - 0-100점, 프로필에 뱃지 표시         │
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
| **스튜디오** | 검증된 강사 풀, 노쇼 보장, 간편한 관리, 투명한 정산 |
| **강사** | 안정적인 일자리, 빠른 정산, 공정한 평가, 이의제기 권리 |
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

### 4.4 수익 모델 (v2.1 전면 개정)

#### 4.4.1 하이브리드 신뢰 모델

| 구분 | Free (기본) | Premium (월 9,900원) |
|------|------------|---------------------|
| **신뢰 방식** | 보증금 50,000원 | **보증금 완전 면제** |
| **거래 수수료** | 5% | **3% (40% 할인)** |
| **매칭 노출** | 기본 노출 | **우선 노출 (상위 30%)** |
| **긴급 매칭** | 미제공 | **2회/월 무료** |
| **고객 지원** | 이메일 24h | **우선 응답 1h** |
| **Trust Score** | 기본 | **+10 보너스** |

#### 4.4.2 Premium 전환율 목표
- 전체 가입자 대비 Premium: **15-20%**
- 보증금 이탈자의 Premium 전환: **30%**
- Premium 평균 구독 유지: **6개월+**
- Premium 월 이탈률: **< 10%**

#### 4.4.3 수익 시뮬레이션 (월 1,000건 거래 기준)
```
Free 사용자 (80%, 800건):
  - 거래 수수료: 800건 × 60만원 × 5% = 24,000,000원

Premium 사용자 (20%, 200명):
  - 구독료: 200명 × 9,900원 = 1,980,000원
  - 거래 수수료: 200건 × 60만원 × 3% = 3,600,000원
  - 소계: 5,580,000원

월 예상 총 매출: 29,580,000원
```

#### 4.4.4 수수료 투명성 정책
```
수수료 부담: 강사 정산 시 차감 (스튜디오 지불 금액에서 5% 공제 후 강사 지급)
과금 시점: 수업 완료 확인 후 정산 시에만 발생
취소된 계약: 수수료 미발생
표시 방법: 계약 확인 화면에 "예상 정산액" 항상 표시

  예) 시급 80,000원 × 8시간 = 640,000원
      플랫폼 수수료 (5%): -32,000원
      예상 정산액: 608,000원
```

### 4.5 초기 결제 거부감 해소 전략 (v2.0 신규)

#### 4.5.1 보증금 진입 시점 지연
```
기존: 가입 → 보증금 결제 → 서비스 이용
변경: 가입 → 프로필 작성 → 공고 탐색 → 매칭 확인 → [지원하기] 클릭 시 보증금 요구

원칙: 앱의 가치를 먼저 경험한 뒤에 결제 유도
      "지원하고 싶은 공고를 찾았다" → 이 시점에 결제 전환율이 가장 높음
```

#### 4.5.2 얼리버드 프로그램
```
런칭 후 3개월간:
  - 보증금: 50,000원 → 30,000원 (40% 할인)
  - 첫 거래 수수료: 5% → 0% (면제)
  - 프로필에 "얼리버드 뱃지" 부여

3개월 이후:
  - 보증금: 정상가 50,000원 적용
  - 수수료: 정상가 5% 적용
  - 기존 얼리버드 사용자: 보증금 차액 추가 납부 불필요 (기존 조건 유지)
```

#### 4.5.3 결제 신뢰 표시
```
결제 화면에 표시할 항목:
  - TossPayments 공식 로고
  - "에스크로로 안전하게 보관됩니다" 문구 + 자물쇠 아이콘
  - "수업 완료 전까지 결제 금액이 안전하게 보관되며, 직접 송금이 아닙니다"
  - 환불 정책 요약 (한 줄)
```

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

#### 6.1.3 자격증 검증 (v2.0 신규)
```
자격증 검증 프로세스:
1. 강사가 자격증 사진/PDF 업로드
2. 운영자 수동 확인 (발급기관, 이름, 유효기간 대조)
3. 검증 완료 시 프로필에 ✓ 마크 부여
4. 유효기간 만료 30일 전 → 자동 알림 발송

검증 기준:
- 발급기관명이 사진에 명시되어 있는가
- 강사 본인 이름과 일치하는가
- 유효기간이 남아있는가

향후 자동화 (Phase 3):
- 주요 발급기관(BASI, STOTT, PMA 등) API 연동 자동 검증
- 유효기간 만료 시 자동으로 ✓ 마크 제거
```

#### 6.1.4 보증금 시스템
- **기본 보증금**: 30,000원 (런칭 프로모션) / 정상가 50,000원
- **충전 방법**: TossPayments 결제
- **결제 시점**: 첫 지원(강사) 또는 첫 오퍼 발송(스튜디오) 시 요구
- **차감 규칙**: 노쇼 확정 시 30,000원
- **환불 조건**: 서비스 탈퇴 시, 패널티 없을 때

#### 6.1.5 온보딩 플로우 (v2.0 신규)
```
강사 온보딩 (3화면):
  화면 1: "프로필을 완성하면 매칭이 시작돼요"
          → 이름, 카테고리, 경력, 지역 입력 (한 화면)
  화면 2: "자격증을 등록하면 신뢰도가 올라가요"
          → 자격증 사진 업로드 (건너뛰기 가능)
  화면 3: "준비 완료! 매칭을 확인해 보세요"
          → 대시보드로 이동 (보증금은 지원 시 안내)

스튜디오 온보딩 (3화면):
  화면 1: "스튜디오 정보를 등록하세요"
          → 상호, 주소, 사업자번호 입력
  화면 2: "어떤 강사가 필요하세요?"
          → 첫 구인공고 작성 유도 (건너뛰기 가능)
  화면 3: "준비 완료! 매칭을 시작하세요"
          → 대시보드로 이동
```

#### 6.1.6 탈퇴 처리 (v2.0 신규)
```
탈퇴 전 확인:
  - 진행 중(CONFIRMED, IN_PROGRESS) 계약이 있으면 → 탈퇴 불가
  - 미정산 금액이 있으면 → 정산 완료 후 탈퇴 가능
  - 보증금 잔액 → 등록된 계좌로 자동 환불

탈퇴 사유 수집 (원탭 설문, 필수):
  ○ 원하는 매칭을 찾지 못했어요
  ○ 결제/수수료가 부담돼요
  ○ 다른 서비스를 이용하게 됐어요
  ○ 앱 사용이 불편했어요
  ○ 분쟁/불쾌한 경험이 있었어요
  ○ 일시적으로 활동을 쉬려고요
  ○ 기타 (자유 입력)

데이터 처리:
  - 탈퇴 즉시: 프로필 비공개, 검색/매칭 제외
  - 30일 후: 개인정보 완전 삭제 (법적 보관 의무 데이터 제외)
  - 계약/정산 기록: 전자상거래법에 따라 5년 보관
  - 리뷰: 닉네임 익명 처리 후 유지
```

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
  ],
  "trust_score": 87
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
  "equipment_brands": ["Gratz", "Balanced Body"],
  "trust_score": 92
}
```

#### 6.2.3 Trust Score (v2.0 신규)
```
Trust Score 산출 (0-100점):
  - 본인인증 완료: +20점 (기본)
  - 보증금 예치: +10점
  - 노쇼 이력: 0회 +30점 / 1회 +15점 / 2회 +5점 / 3회 이상 0점
  - 리뷰 평균: (평균점수/5) × 25점
  - 계약 완료 횟수: min(완료횟수, 20) / 20 × 15점

표시 방식:
  - 프로필 카드에 Trust Score 뱃지
  - 90-100: 🟢 Trusted / 70-89: 🔵 Reliable / 50-69: 🟡 Growing / 50 미만: 표시 안 함
  - 매칭 리스트에서 Trust Score 정렬 옵션 제공
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

#### 6.4.2 계약 상태 머신 (v2.0 개선)
```
        [CONFIRMED]
            │
            ├─→ [IN_PROGRESS] (결제 완료)
            │       │
            │       ├─→ [PENDING_COMPLETION] (수업 종료, 양측 확인 대기)
            │       │       │
            │       │       ├─→ [COMPLETED] (양측 확인 완료)
            │       │       └─→ [DISPUTED] (완료 거부 → 분쟁)
            │       │
            │       └─→ [CANCELLED] (취소+환불)
            │
            └─→ [CANCELLED] (취소)
```

#### 6.4.3 수업 완료 상호 확인 (v2.0 신규)
```
수업 종료 시각 도래
  ↓
양측에 "수업 완료 확인" 푸시 알림 발송
  ↓
스튜디오: "수업 완료 확인" 원탭
강사: "수업 완료 확인" 원탭
  ↓
양측 확인 → COMPLETED → 에스크로 RELEASED → 정산 시작

예외 처리:
  - 한쪽만 확인, 24시간 경과 → 자동 완료 처리 + 미확인 측 알림
  - 양측 미확인, 48시간 경과 → 자동 완료 처리 + 양측 알림
  - 완료 거부 (문제 발생) → DISPUTED → 분쟁 해결 프로세스 진입
```

#### 6.4.4 계약 진행 타임라인 UI (v2.0 신규)
```
계약 상세 화면 상단에 진행 바 표시:

  [✓ 계약체결] ─→ [✓ 결제완료] ─→ [● 수업진행] ─→ [○ 완료확인] ─→ [○ 정산]

각 단계 탭 시:
  - 완료 시각, 담당자, 관련 이벤트 로그 표시

현재 단계에서 필요한 액션을 CTA 버튼으로 표시:
  "수업이 완료되었나요?" → [수업 완료 확인]
```

#### 6.4.5 계약 이벤트 로그
모든 상태 전환 기록:
- 행위자 (actor_user_id)
- 이전 상태 → 새 상태
- 변경 시각
- 사유 (note)

### 6.5 결제 시스템

#### 6.5.1 에스크로 결제 (v2.0 개선)
```
1. 계약 확정
   ↓
2. 스튜디오 결제 (TossPayments)
   - 결제 화면에 TossPayments 로고 + 에스크로 안내 문구 표시
   - "예상 정산액" 실시간 계산 표시
   ↓
3. 에스크로 HELD (플랫폼 보관)
   ↓
4. 수업 진행
   ↓
5. 양측 완료 확인 (6.4.3 참조)
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

#### 6.5.3 환불 정책 고지 타이밍 (v2.0 신규)
```
사용자가 정책을 인지하는 시점:

1. 계약 체결 직전
   - 계약 확인 화면에 환불 조건 요약 고정 표시
   - "24시간 전 100% / 24시간 이내 70% / 수업 시작 후 환불 불가"
   - "취소/환불 정책에 동의합니다" 체크박스 필수 → 동의 시각 기록

2. 결제 완료 시
   - 영수증에 환불 정책 포함

3. 취소 요청 시 (실시간 계산)
   - "지금 취소하면 56,000원(70%)이 환불됩니다. 취소하시겠습니까?"
   - 환불 비율이 시간에 따라 변하는 것을 시각적으로 표시

4. 계약 상세 화면
   - 항상 접근 가능한 "취소/환불 정책" 링크
```

#### 6.5.4 정산 내역 투명성 (v2.0 신규)
```
강사 정산 내역 (계약 건별):
  - 계약번호: #CTR-20260220-001
  - 스튜디오: 강남 필라테스
  - 수업일시: 2026-02-20 10:00-18:00 (8시간)
  - 시급: 80,000원
  - 총 금액: 640,000원
  - 플랫폼 수수료 (5%): -32,000원
  - 정산 금액: 608,000원
  - 정산 상태: 정산 완료 (2026-02-22)
  - 입금 계좌: ○○은행 ****1234

월간 정산 요약:
  - 총 계약 건수 / 총 수업 시간 / 총 수입
  - 총 수수료 / 순 정산액
  - 이전 월 대비 증감 (▲▼)
```

### 6.6 신뢰 시스템

#### 6.6.1 노쇼 판정 (v2.0 개선 — 공정성 강화)
```
기존: 스튜디오 신고 → 즉시 차감 (강사 항변 기회 없음)

개선:
1. 스튜디오가 "노쇼 신고" 접수
2. 강사에게 즉시 알림: "노쇼 신고가 접수되었습니다"
3. 24시간 이의제기 기간 부여
   - 이의제기 없음 → 패널티 자동 확정
     · no_show_count += 1
     · deposit_balance -= 30,000
     · if no_show_count >= 3: is_suspended = True
     · 스튜디오 전액 환불
   - 이의제기 있음 → 보증금 차감 보류 → 분쟁 해결 프로세스 진입

노쇼 판정 보조 데이터 (자동 수집):
  - 강사의 마지막 앱 접속 시각
  - 수업 당일 채팅 기록 유무
  - 수업 전 리마인더 확인 여부
```

#### 6.6.2 분쟁 해결 프로세스 (v2.0 신규)
```
┌────────────────────────────────────────────────────┐
│        분쟁 해결 — 1인 운영자 최적화 설계           │
├────────────────────────────────────────────────────┤
│                                                    │
│ 1단계: 자동 조정 (즉시)                             │
│   · 노쇼/완료거부 시 상대방에 24h 이의제기 기간 부여 │
│   · 이의제기 없으면 → 자동 확정 (운영자 개입 불필요) │
│   · 이의제기 있으면 → 2단계 이관                     │
│                                                    │
│ 2단계: 증거 기반 심사 (48시간 이내)                  │
│   · 시스템이 자동으로 분쟁 리포트 생성:              │
│     - 해당 계약의 채팅 기록                          │
│     - 양측 알림 확인 이력                            │
│     - 앱 접속 로그                                   │
│     - 리마인더 확인 여부                             │
│   · 관리자 대시보드에 분쟁 건 목록 표시               │
│   · 판정 버튼: [강사측 확정] [스튜디오측 확정]       │
│                [양측 부분책임]                        │
│   · 판정 결과 + 사유를 양측에 자동 통보              │
│                                                    │
│ 3단계: 최종 이의 (7일 이내)                         │
│   · 2단계 결과에 불복 시 이메일로 최종 이의 가능     │
│   · 1회 한정, 운영자 최종 판정 → 확정               │
│                                                    │
│ 예상 규모 (월 거래 1,000건 기준):                   │
│   · 노쇼/분쟁 발생: 30-50건 (3-5%)                 │
│   · 자동 처리 (이의제기 없음): 25-45건              │
│   · 운영자 개입 필요: 5-15건/월 (혼자 감당 가능)    │
│                                                    │
└────────────────────────────────────────────────────┘
```

#### 6.6.3 리뷰 시스템
- **작성 권한**: 계약 완료 후 7일 이내
- **평가 항목**:
  - 전문성 (1-5점)
  - 시간 준수 (1-5점)
  - 커뮤니케이션 (1-5점)
  - 종합 만족도 (1-5점)
- **리뷰 공개**: 양방향 작성 완료 후

#### 6.6.4 신고/차단
- **신고 사유**: 허위 프로필, 부적절한 행동, 노쇼, 기타
- **처리 절차**: 접수 → 검토 → 조치 → 통보
- **차단 효과**: 상호 프로필 비표시, 매칭 제외

### 6.7 커뮤니케이션

#### 6.7.1 실시간 채팅
- **채팅방 생성**: 계약 체결 시 자동
- **참여자**: 강사, 스튜디오
- **메시지 유형**: 텍스트, 시스템 알림
- **실시간 전송**: WebSocket

#### 6.7.2 알림 시스템 (v2.0 개선)
| 이벤트 | 수신자 | 알림 방식 |
|--------|--------|----------|
| 새 지원서 | 스튜디오 | 인앱, 이메일 |
| 오퍼 수신 | 강사 | 인앱, SMS |
| 계약 체결 | 양측 | 인앱, 이메일 |
| 수업 리마인더 | 양측 | SMS (D-1) |
| 수업 완료 확인 요청 | 양측 | 인앱, SMS |
| 노쇼 신고 접수 | 피신고자 | 인앱, 이메일, SMS |
| 이의제기 기간 만료 임박 | 피신고자 | SMS (만료 6시간 전) |
| 분쟁 판정 결과 | 양측 | 인앱, 이메일 |
| 정산 완료 | 강사 | 인앱 |

#### 6.7.3 통합 활동 피드 (v2.0 신규)
```
대시보드 상단에 시간순 활동 피드:
  · 모든 이벤트를 한 화면에 표시
  · 각 알림에서 바로 액션 가능 (지원 확인, 오퍼 수락, 완료 확인 등)
  · 읽지 않은 항목 뱃지
  · 필터: 전체 / 지원 관련 / 계약 관련 / 정산 관련

예시:
  [14:30] 📋 "주말 대체 강사" 공고에 새 지원서 2건 → [확인하기]
  [13:00] 💰 계약 #1234 정산 완료 (608,000원 입금) → [상세보기]
  [10:15] ⚠️ 내일 10:00 수업 리마인더 (강남점) → [일정보기]
```

### 6.8 법적 기반 (v2.0 신규)

#### 6.8.1 필수 약관
```
가입 시 동의 필수:
  - 서비스 이용약관
  - 개인정보 수집 및 이용 동의
  - 제3자 정보 제공 동의 (결제사, SMS 발송 등)
  - 전자금융거래 이용약관 (에스크로 관련)

선택 동의:
  - 마케팅 수신 동의 (이메일, SMS)
  - 위치정보 이용 동의 (향후 GPS 체크인 기능 시)

약관 관리:
  - 약관 변경 시 사용자에게 재동의 요청
  - 동의 이력 (약관 버전, 동의 시각) DB 기록
```

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
│  │Payment  │ │Dispute  │ │  Chat   │   │
│  │ Service │ │ Service │ │ Service │   │
│  └─────────┘ └─────────┘ └─────────┘   │
│  ┌─────────┐ ┌──────────────────────┐   │
│  │Analytics│ │ Scheduled Jobs       │   │
│  │ Service │ │ (Churn, Auto-close)  │   │
│  └─────────┘ └──────────────────────┘   │
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
│ Google Analytics / Mixpanel (Free tier)  │
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
| **Queue** | Celery | 5+ | 비동기 작업, 스케줄 작업 |
| **Container** | Docker | 24+ | 컨테이너화 |
| **Frontend** | Streamlit | 1.30+ | MVP UI |
| **Monitoring** | Prometheus | - | 메트릭 수집 |
| **Analytics** | Mixpanel Free | - | 퍼널 분석, 이탈 추적 |

### 8.3 마이크로서비스 구조 (Future)
```
services/
├── auth-service/        # 인증/인가
├── user-service/        # 사용자 관리
├── matching-service/    # 매칭 엔진
├── contract-service/    # 계약 관리
├── payment-service/     # 결제 처리
├── dispute-service/     # 분쟁 처리
├── notification-service/# 알림 발송
└── analytics-service/   # 데이터 분석, 이탈 추적
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
    trust_score INTEGER DEFAULT 0,

    -- Premium Membership (v2.1)
    membership_tier VARCHAR(20) DEFAULT 'free',  -- 'free' | 'premium'

    -- Activity Tracking (v2.0)
    last_active_at TIMESTAMP,
    onboarding_completed BOOLEAN DEFAULT FALSE,

    -- Timestamps
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);
```

#### contracts (v2.0 개선)
```sql
CREATE TABLE contracts (
    id VARCHAR(36) PRIMARY KEY,
    offer_id VARCHAR(36) REFERENCES offers(id),
    studio_id VARCHAR(36) REFERENCES studio_profiles(id),
    instructor_id VARCHAR(36) REFERENCES instructor_profiles(id),

    status VARCHAR(20) NOT NULL,  -- CONFIRMED/IN_PROGRESS/PENDING_COMPLETION/COMPLETED/DISPUTED/CANCELLED
    date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    hourly_rate NUMERIC(10,2) NOT NULL,
    total_amount NUMERIC(10,2) NOT NULL,
    platform_fee NUMERIC(10,2) DEFAULT 0,
    settlement_amount NUMERIC(10,2) DEFAULT 0,

    -- Completion confirmation (v2.0)
    studio_confirmed_at TIMESTAMP,
    instructor_confirmed_at TIMESTAMP,

    -- Cancellation/Refund policy agreement (v2.0)
    policy_agreed_at TIMESTAMP,
    policy_version VARCHAR(10),

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

#### disputes (v2.0 신규)
```sql
CREATE TABLE disputes (
    id VARCHAR(36) PRIMARY KEY,
    contract_id VARCHAR(36) REFERENCES contracts(id),
    reported_by VARCHAR(36) REFERENCES users(id),
    reported_against VARCHAR(36) REFERENCES users(id),

    type VARCHAR(20) NOT NULL,         -- 'no_show' | 'completion_rejected' | 'other'
    status VARCHAR(20) NOT NULL,       -- 'OPEN' | 'OBJECTED' | 'RESOLVED'
    objection_deadline TIMESTAMP,      -- 이의제기 마감 시각
    objection_reason TEXT,             -- 이의제기 사유
    resolution VARCHAR(20),            -- 'reporter_wins' | 'respondent_wins' | 'partial'
    resolution_reason TEXT,
    resolved_by VARCHAR(36),           -- 'system' | admin_user_id
    resolved_at TIMESTAMP,

    -- Auto-collected evidence (v2.0)
    evidence_snapshot JSONB,           -- 채팅기록, 접속로그, 리마인더확인 등 자동 수집

    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);
```

#### user_churn_log (v2.0 신규)
```sql
CREATE TABLE user_churn_log (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) REFERENCES users(id),
    event_type VARCHAR(20) NOT NULL,   -- 'withdrawal' | 'dormant_30d' | 'dormant_60d'
    reason_code VARCHAR(50),           -- 탈퇴 사유 코드
    reason_detail TEXT,                -- 기타 사유 자유입력
    created_at TIMESTAMP NOT NULL
);
```

#### policy_agreements (v2.0 신규)
```sql
CREATE TABLE policy_agreements (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) REFERENCES users(id),
    policy_type VARCHAR(50) NOT NULL,  -- 'terms_of_service' | 'privacy' | 'refund' | 'escrow'
    policy_version VARCHAR(10) NOT NULL,
    agreed_at TIMESTAMP NOT NULL
);
```

#### subscriptions (v2.1 신규)
```sql
CREATE TABLE subscriptions (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) REFERENCES users(id) UNIQUE,

    -- Subscription details
    tier VARCHAR(20) DEFAULT 'premium',
    status VARCHAR(20) DEFAULT 'inactive',  -- inactive/active/cancelled/expired/suspended

    -- Billing
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    next_billing_date TIMESTAMP,
    billing_cycle_day INTEGER,
    monthly_amount NUMERIC(10,2) DEFAULT 9900,
    auto_renew BOOLEAN DEFAULT TRUE,

    -- Cancellation
    cancelled_at TIMESTAMP,
    cancellation_reason TEXT,

    -- Payment method
    toss_billing_key VARCHAR(200),
    payment_method_type VARCHAR(50),

    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE INDEX idx_subscription_user ON subscriptions(user_id);
CREATE INDEX idx_subscription_status ON subscriptions(status);
CREATE INDEX idx_subscription_billing ON subscriptions(next_billing_date);
```

#### subscription_payments (v2.1 신규)
```sql
CREATE TABLE subscription_payments (
    id VARCHAR(36) PRIMARY KEY,
    subscription_id VARCHAR(36) REFERENCES subscriptions(id),

    -- Payment details
    amount NUMERIC(10,2) DEFAULT 9900,
    status VARCHAR(20) DEFAULT 'pending',  -- pending/completed/failed/refunded
    payment_date TIMESTAMP,
    due_date TIMESTAMP,

    -- TossPayments
    order_id VARCHAR(200) UNIQUE,
    toss_payment_key VARCHAR(200) UNIQUE,

    -- Error handling
    failure_reason TEXT,
    retry_count INTEGER DEFAULT 0,
    last_retry_at TIMESTAMP,

    receipt_url VARCHAR(500),

    created_at TIMESTAMP,
    updated_at TIMESTAMP
);

CREATE INDEX idx_payment_subscription ON subscription_payments(subscription_id);
CREATE INDEX idx_payment_status ON subscription_payments(status);
```

#### subscription_history (v2.1 신규)
```sql
CREATE TABLE subscription_history (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) REFERENCES users(id),

    -- Change details
    old_tier VARCHAR(20),
    new_tier VARCHAR(20),
    reason VARCHAR(50),  -- upgrade/downgrade/auto_renew/cancellation

    note TEXT,
    performed_by VARCHAR(36),
    payment_id VARCHAR(36),

    created_at TIMESTAMP
);

CREATE INDEX idx_history_user ON subscription_history(user_id);
CREATE INDEX idx_history_created ON subscription_history(created_at);
```

### 9.2 인덱스 전략
```sql
-- 성능 최적화 인덱스
CREATE INDEX idx_job_posts_status_region ON job_posts(status, region);
CREATE INDEX idx_applications_job_instructor ON applications(job_post_id, instructor_id);
CREATE INDEX idx_contracts_status_date ON contracts(status, date);
CREATE INDEX idx_users_role_verified ON users(role, identity_verified);

-- v2.0 추가 인덱스
CREATE INDEX idx_disputes_status ON disputes(status);
CREATE INDEX idx_disputes_deadline ON disputes(objection_deadline) WHERE status = 'OPEN';
CREATE INDEX idx_users_last_active ON users(last_active_at);
CREATE INDEX idx_users_trust_score ON users(trust_score);
```

### 9.3 데이터 보관 정책
| 데이터 유형 | 보관 기간 | 처리 방법 |
|------------|----------|----------|
| 활성 계약 | 무제한 | - |
| 완료 계약 | 5년 | 아카이브 |
| 채팅 메시지 | 1년 | 삭제 |
| 로그 데이터 | 3개월 | S3 이동 |
| 삭제된 사용자 | 30일 | 완전 삭제 |
| 정산 기록 | 5년 | 전자상거래법 준수 |
| 약관 동의 이력 | 5년 | 법적 증빙 |
| 분쟁 기록 | 3년 | 아카이브 |
| 이탈 사유 로그 | 2년 | 분석 후 삭제 |

---

## 10. API 설계

### 10.1 API 구조
```
Base URL: https://api.StudioBridge.com/api/v1

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

#### Contracts (v2.0 개선)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /contracts/from-offer/{id} | 계약 생성 |
| GET | /contracts/me | 내 계약 목록 |
| POST | /contracts/{id}/set-in-progress | 진행 시작 |
| POST | /contracts/{id}/confirm-completion | 완료 확인 (v2.0) |
| POST | /contracts/{id}/reject-completion | 완료 거부 → 분쟁 (v2.0) |
| POST | /contracts/{id}/cancel | 취소 |
| POST | /contracts/{id}/report-no-show | 노쇼 신고 |
| GET | /contracts/{id}/timeline | 진행 타임라인 (v2.0) |

#### Disputes (v2.0 신규)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /disputes/me | 내 분쟁 목록 |
| POST | /disputes/{id}/object | 이의제기 |
| GET | /disputes/{id}/evidence | 증거 리포트 조회 |

#### Settlements (v2.0 신규)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /settlements/me | 내 정산 내역 |
| GET | /settlements/me/summary | 월간 정산 요약 |

#### Admin — Disputes (v2.0 신규)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /admin/disputes | 미처리 분쟁 목록 |
| GET | /admin/disputes/{id}/report | 자동 수집 증거 리포트 |
| POST | /admin/disputes/{id}/resolve | 분쟁 판정 |

#### Admin — Analytics (v2.0 신규)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /admin/churn/dormant | 이탈 위험 사용자 목록 |
| GET | /admin/churn/reasons | 탈퇴 사유 통계 |

#### Subscriptions (v2.1 신규)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /subscriptions/me | 내 구독 정보 |
| POST | /subscriptions/upgrade | Premium 업그레이드 시작 |
| POST | /subscriptions/confirm | 결제 확인 |
| POST | /subscriptions/cancel | 구독 취소 |
| GET | /subscriptions/history | 변경 이력 조회 |

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
        "field": "field_name"
    }
}
```

#### 페이지네이션
```json
{
    "items": [],
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
| DISPUTE_PENDING | 409 | 분쟁 진행 중 (v2.0) |
| ACTIVE_CONTRACT_EXISTS | 400 | 진행 중 계약 있음 — 탈퇴 불가 (v2.0) |

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

### 13.2 핵심 플로우 최대 스텝 제한 (v2.0 신규)
| 플로우 | 목표 최대 스텝 | 설계 원칙 |
|--------|--------------|----------|
| 회원가입 → 본인인증 완료 | **4 이하** | 가입과 인증을 한 화면에 통합 |
| 구인공고 등록 | **3 이하** | 한 화면 폼 + 요약 확인 + 게시 |
| 공고 발견 → 지원 완료 | **2 이하** | 리스트에서 원탭 지원 (프로필 자동 첨부) |
| 오퍼 수신 → 수락 | **2 이하** | 알림에서 바로 오퍼 확인 → 수락 |
| 수업 완료 확인 | **1** | 대시보드 배너에서 원탭 확인 |
| 환불 요청 | **2 이하** | 계약 상세에서 취소 → 환불액 확인 → 확정 |

### 13.3 주요 화면

#### 13.3.1 대시보드 (v2.0 개선)
```
┌─────────────────────────────────┐
│      📢 활동 피드 (3건 읽지않음) │
├─────────────────────────────────┤
│ [14:30] 📋 새 지원서 2건       │
│  → [확인하기]                   │
│ [13:00] 💰 정산완료 608,000원  │
│  → [상세보기]                   │
├─────────────────────────────────┤
│         오늘의 일정 (2)         │
├─────────────────────────────────┤
│ 10:00 - 강남점 필라테스 수업    │
│  → [수업 완료 확인]  ← 원탭 CTA │
│ 14:00 - 서초점 요가 수업        │
├─────────────────────────────────┤
│         새로운 매칭 (5)         │
├─────────────────────────────────┤
│ [92%] 🟢 주말 대체 강사        │
│ [85%] 🔵 평일 오전 강사        │
└─────────────────────────────────┘
```

#### 13.3.2 매칭 리스트
```
┌─────────────────────────────────┐
│   📍 서울 강남 | 💰 80,000원    │
│   주말 필라테스 강사 구합니다   │
│   [Perfect Match 95%] 🟢       │
│   📅 2026-02-20 | ⏰ 10:00-18:00│
│   [지원하기]                   │
├─────────────────────────────────┤
│   📍 서울 서초 | 💰 70,000원    │
│   평일 요가 강사 구합니다       │
│   [Great Match 82%] 🔵         │
│   📅 2026-02-21 | ⏰ 09:00-12:00│
│   [지원하기]                   │
└─────────────────────────────────┘
```

### 13.4 빈 상태 & 에러 상태 가이드 (v2.0 신규)
```
빈 상태:
  매칭 없음:
    "아직 새로운 매칭이 없어요. 프로필을 완성하면 더 많은 매칭을 받을 수 있어요!"
    → [프로필 완성하기]

  계약 없음:
    "첫 계약을 기다리고 있어요. 공고를 둘러볼까요?"
    → [공고 보러가기]

  리뷰 없음:
    "아직 리뷰가 없어요. 첫 수업을 완료하면 리뷰를 받을 수 있어요."

에러 상태:
  결제 실패:
    "결제가 완료되지 않았어요. 다시 시도하거나 다른 결제 수단을 이용해 주세요."
    → [다시 시도] [다른 수단]
  네트워크 오류:
    "연결이 불안정해요. 잠시 후 다시 시도해 주세요."
    → [새로고침]
```

### 13.5 모바일 UI 가이드라인
- **터치 타겟**: 최소 44x44 px
- **폰트 크기**: 본문 16px 이상
- **컬러 대비**: WCAG AA 기준
- **제스처**: 스와이프, 풀 투 리프레시

### 13.6 접근성
- **스크린 리더**: 모든 요소 라벨링
- **키보드 네비게이션**: Tab 순서 지정
- **색맹 대응**: 색상만으로 구분 금지
- **다국어**: 한국어, 영어 지원

### 13.7 Premium 멤버십 UI/UX (v2.1 신규)

#### 13.7.1 멤버십 선택 화면
```
┌─────────────────────────────────────┐
│     어떤 방식으로 시작할까요?       │
├─────────────────────────────────────┤
│                                     │
│  ┌──────────┐    ┌──────────┐      │
│  │   Free   │    │ Premium  │      │
│  │          │    │ ⭐ 추천   │      │
│  └──────────┘    └──────────┘      │
│                                     │
│  보증금 필요      보증금 불필요      │
│  50,000원        월 9,900원         │
│                                     │
│  수수료 5%       수수료 3%          │
│  기본 노출       우선 노출          │
│                                     │
│  [선택하기]      [선택하기]         │
│                                     │
└─────────────────────────────────────┘
```

#### 13.7.2 보증금 결제 시점 Premium 제안
```
┌─────────────────────────────────────┐
│  💡 월 9,900원으로 더 편리하게       │
├─────────────────────────────────────┤
│                                     │
│  보증금 50,000원 대신                │
│  Premium으로 시작하시겠어요?         │
│                                     │
│  ✓ 보증금 완전 면제                 │
│  ✓ 수수료 40% 할인                  │
│  ✓ 우선 노출로 빠른 매칭             │
│                                     │
│  [Premium 시작]   [보증금 결제]      │
│                                     │
└─────────────────────────────────────┘
```

#### 13.7.3 멤버십 상태 표시

**대시보드 상단 (Free 회원)**:
```
┌─────────────────────────────────────┐
│ 💎 Premium으로 업그레이드하고        │
│    보증금 50,000원을 돌려받으세요    │
│    [자세히 보기]          [✕ 닫기]  │
└─────────────────────────────────────┘
```

**대시보드 상단 (Premium 회원)**:
```
┌─────────────────────────────────────┐
│ ⭐ Premium 회원                      │
│ 다음 결제: 2026-03-15 (9,900원)     │
│ [구독 관리]                          │
└─────────────────────────────────────┘
```

#### 13.7.4 매칭 리스트 우선 노출
- Premium 회원의 프로필 상위 30% 배치
- 프로필에 "⭐ Premium" 뱃지 표시
- Trust Score와 무관하게 우선 노출

---

## 14. 운영 설계 (1인 개발자) (v2.0 신규)

> 핵심 원칙: "시스템이 자동으로 처리하고, 사람은 예외만 다룬다"

### 14.1 자동화 vs 수동 개입 기준

| 상황 | 처리 방식 | 운영자 개입 |
|------|----------|-----------|
| 노쇼 신고 → 이의제기 없음 | 자동 확정 | 불필요 |
| 취소/환불 요청 | 정책 기반 자동 처리 | 불필요 |
| 수업 완료 확인 timeout | 48시간 후 자동 완료 | 불필요 |
| 노쇼 이의제기 발생 | 증거 리포트 자동 생성 | 판정만 수동 |
| 완료 거부 분쟁 | 증거 리포트 자동 생성 | 판정만 수동 |
| 자격증 검증 | 사진 업로드 | 확인만 수동 |
| 신고 접수 | 알림 자동 | 검토만 수동 |

### 14.2 관리자 대시보드

```
┌────────────────────────────────────────┐
│         StudioBridge Admin Dashboard      │
├────────────────────────────────────────┤
│                                        │
│  ⚠️ 처리 필요                          │
│  ├─ 미처리 분쟁: 3건     → [바로가기]   │
│  ├─ 자격증 검증 대기: 5건 → [바로가기]   │
│  └─ 신고 접수: 1건       → [바로가기]   │
│                                        │
│  📊 오늘 현황                           │
│  ├─ 신규 가입: 12명                     │
│  ├─ 거래 완료: 34건                     │
│  ├─ 거래액: 4,200,000원                 │
│  └─ 에러율: 0.08%                       │
│                                        │
│  🔔 이탈 경고                           │
│  ├─ 7일 미접속: 28명    → [리마인더발송] │
│  ├─ 가입 후 미지원: 15명 → [넛지 발송]   │
│  └─ 3회 거절 강사: 2명  → [프로필팁발송] │
│                                        │
│  📈 이탈 분석 (이번 달)                 │
│  ├─ 탈퇴: 8명                           │
│  │  매칭 못 찾음: 3 / 수수료 부담: 2    │
│  │  다른 서비스: 1 / 불편: 1 / 휴식: 1  │
│  └─ 조용한 이탈 (30일+): 45명           │
│                                        │
│  분쟁 처리:                             │
│  ┌──────────────────────────────────┐  │
│  │ 분쟁 #D-001                      │  │
│  │ 계약: #CTR-20260218-003         │  │
│  │ 유형: 노쇼 이의제기              │  │
│  │ 신고자: 강남 필라테스 (스튜디오)  │  │
│  │ 피신고: 이필라 (강사)            │  │
│  │                                  │  │
│  │ 자동 수집 증거:                   │  │
│  │ · 강사 마지막 접속: 수업일 08:30 │  │
│  │ · 채팅: 전날 "내일 뵙겠습니다"   │  │
│  │ · 리마인더 확인: ✓               │  │
│  │ · 이의제기 사유: "스튜디오에서    │  │
│  │   주소를 잘못 알려줘서 못 갔음"   │  │
│  │                                  │  │
│  │ [강사측 확정] [스튜디오측 확정]   │  │
│  │ [양측 부분책임]                   │  │
│  └──────────────────────────────────┘  │
│                                        │
└────────────────────────────────────────┘
```

### 14.3 스케줄 작업 (Celery Beat)

```python
# 자동화 스케줄 작업 목록

매 시간:
  - 이의제기 마감 체크 → 마감 도래 시 패널티 자동 확정
  - 수업 완료 48시간 미확인 → 자동 완료 처리

매일 09:00:
  - 수업 리마인더 발송 (D-1)
  - 7일 미접속 사용자 → 리마인드 푸시/SMS
  - 자격증 유효기간 만료 30일 전 알림

매일 21:00:
  - 가입 후 3일 경과 + 지원 0건 → "첫 지원을 도와드릴까요?" 알림
  - 지원 3회 연속 거절 강사 → "프로필 개선 팁" 발송

매주 월요일 10:00:
  - 30일 미접속 사용자 목록 → "혹시 불편한 점이 있으셨나요?" 이메일
  - 주간 이탈/분쟁/거래 통계 → 관리자 이메일 리포트

매월 1일:
  - 월간 정산 요약 생성 (강사별)
  - 이탈 사유 통계 집계
  - Trust Score 일괄 재계산
```

### 14.4 고객 지원 채널

```
지원 채널 (우선순위):
  1. 인앱 1:1 문의: 채팅 형식, 관리자 대시보드에서 응답
  2. 이메일 (support@StudioBridge.com): 복잡한 분쟁, 서류 첨부 필요 시
  3. FAQ/도움말 센터: 자주 묻는 질문 자체 해결 유도

운영 시간: 평일 09:00-21:00 / 주말 10:00-18:00
긴급 대응: 수업 당일 노쇼/사고 시 긴급 연락처 (전화) 운영
응답 목표: 인앱 문의 1시간 이내 / 이메일 24시간 이내
```

### 14.5 이탈 추적 시스템 (v2.0 신규)

#### 14.5.1 이탈 전 신호 감지 (Churn Signal)
```
서버 로그 + DB 쿼리 기반 (별도 분석 도구 불필요):

위험 신호 1: 7일 이상 미접속
  → 자동 푸시/SMS: "새로운 매칭 N건이 기다리고 있어요"

위험 신호 2: 가입 후 3일 경과, 지원 0건
  → 자동 알림: "첫 지원을 도와드릴까요? 지금 N건의 매칭이 있어요"

위험 신호 3: 지원 3회 이상 연속 거절
  → 자동 알림: "프로필 개선 팁" + 추천 자격증/지역 제안

위험 신호 4: 보증금 결제 화면에서 이탈
  → 다음 접속 시 보증금 안내 배너: "안전한 에스크로 결제, 부담 없이 시작하세요"
```

#### 14.5.2 조용한 이탈 대응
```
30일 미접속 사용자:
  → 이메일: "혹시 불편한 점이 있으셨나요? 한 줄이라도 알려주시면 개선하겠습니다."
  → 회신 내용을 user_churn_log에 수동 기록

60일 미접속 사용자:
  → 최종 리마인드: "계정이 휴면 전환 예정입니다. 다시 활동하시려면 로그인해 주세요."

90일 미접속:
  → 휴면 계정 전환 (매칭 제외, 프로필 비노출)
  → 언제든 로그인하면 즉시 복구
```

#### 14.5.3 퍼널 분석 (Mixpanel Free Tier)
```
추적할 핵심 퍼널:

강사 퍼널:
  가입 → 프로필 완성 → 보증금 결제 → 첫 지원 → 첫 계약 → 재계약
  (각 단계별 이탈률 추적)

스튜디오 퍼널:
  가입 → 프로필 완성 → 첫 공고 → 첫 오퍼 → 첫 계약 → 재공고
  (각 단계별 이탈률 추적)

핵심 확인 지표:
  - 어느 단계에서 가장 많이 이탈하는가?
  - 보증금 결제 전환율은 얼마인가?
  - 첫 계약까지 평균 며칠 걸리는가?
```

---

## 15. 배포 및 인프라

### 15.1 환경 구성
| Environment | Purpose | URL |
|-------------|---------|-----|
| Development | 개발 | dev.StudioBridge.com |
| Staging | 테스트 | staging.StudioBridge.com |
| Production | 운영 | StudioBridge.com |

### 15.2 배포 전략
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

### 15.3 모니터링
| 도구 | 용도 | 메트릭 |
|------|------|--------|
| Prometheus | 메트릭 수집 | CPU, Memory, Requests |
| Grafana | 시각화 | 대시보드 |
| ELK Stack | 로그 분석 | 에러율, 패턴 |
| Sentry | 에러 추적 | Exception, Stack trace |
| Datadog | APM | Transaction, Trace |

### 15.4 백업 및 복구
- **데이터베이스**: 일일 전체 백업, 시간별 증분 백업
- **파일 스토리지**: S3 versioning
- **복구 목표**: RTO 1시간, RPO 1시간
- **재해 복구**: Multi-region 구성

### 15.5 운영 체크리스트
```
Daily:
□ 서비스 가용성 확인
□ 에러율 모니터링
□ 미처리 분쟁 건 확인 (관리자 대시보드)
□ 자격증 검증 대기 처리

Weekly:
□ 성능 메트릭 리뷰
□ 보안 로그 검토
□ 백업 상태 확인
□ 이탈 위험 사용자 리마인드 확인
□ 이탈 사유 리뷰

Monthly:
□ 보안 패치 적용
□ 의존성 업데이트
□ 비용 최적화
□ 퍼널 분석 리뷰 (어디서 이탈하는가?)
□ 탈퇴 사유 통계 분석 → 개선 항목 도출
```

---

## 16. 성공 지표

### 16.1 비즈니스 KPI
| 지표 | 목표 (6개월) | 측정 방법 |
|------|------------|-----------|
| MAU | 5,000명 | Google Analytics |
| 거래 전환율 | 30% | 지원→계약 비율 |
| 월 거래액 | 1억원 | 결제 시스템 |
| 재사용률 | 60% | 코호트 분석 |
| NPS | 50+ | 설문조사 |

### 16.2 기술 지표
| 지표 | 목표 | 현재 |
|------|------|------|
| 가용성 | 99.9% | 99.5% |
| 평균 응답시간 | < 200ms | 180ms |
| 에러율 | < 0.1% | 0.15% |
| 테스트 커버리지 | > 80% | 72% |

### 16.3 사용자 만족도
- **앱 평점**: 4.5/5.0 이상
- **리뷰 응답률**: 100%
- **CS 응답시간**: 1시간 이내
- **이탈률**: < 20%

### 16.4 신뢰 지표 (v2.0 신규)
| 지표 | 목표 (6개월) | 측정 방법 |
|------|------------|-----------|
| 분쟁 발생률 | < 5% | 분쟁 건수 / 총 거래 |
| 분쟁 자동 해결률 | > 70% | 이의제기 없이 확정 비율 |
| 노쇼율 | < 3% | 노쇼 건수 / 총 계약 |
| 평균 Trust Score | 75+ | 활성 사용자 평균 |
| 보증금 결제 전환율 | > 60% | 가입 → 보증금 결제 |

### 16.5 이탈 지표 (v2.0 신규)
| 지표 | 목표 (6개월) | 측정 방법 |
|------|------------|-----------|
| 월간 탈퇴율 | < 5% | 탈퇴자 / MAU |
| 30일 휴면 전환율 | < 15% | 30일 미접속 / 전체 |
| 첫 계약까지 소요일 | < 7일 | 가입~첫 계약 중위값 |
| 보증금 이탈률 | < 40% | 보증금 화면 진입→미결제 |
| 탈퇴 사유 1위 | 추적 | 탈퇴 설문 분석 |

### 16.6 Premium 멤버십 지표 (v2.1 신규)
| 지표 | 목표 (6개월) | 측정 방법 |
|------|------------|-----------|
| Premium 전환율 | 15-20% | Premium 가입자 / 전체 가입자 |
| 보증금 이탈 → Premium | 30% | 보증금 실패 후 Premium 선택 |
| Premium LTV | 60,000원 | 평균 6개월 × 9,900원 |
| Premium Churn | < 10%/월 | 월 취소율 |
| Premium ARPU | 50,000원/월 | Premium 총 매출 / Premium 사용자 |
| Premium 재가입률 | 40% | 취소 후 3개월 내 재가입 |
| 결제 성공률 | > 95% | 성공 / 전체 결제 시도 |

---

## 17. 로드맵

### 17.1 Phase 1: MVP (현재)
**기간**: 2026.01 - 2026.02 ✅
- [x] 핵심 기능 구현
- [x] 신뢰 시스템 구축
- [x] 결제 시스템 연동
- [x] 기본 UI 개발

### 17.2 Phase 1.5: Premium 출시 & 운영 준비 (v2.1 개정)
**기간**: 2026.02 - 2026.03
- [x] **Premium 멤버십 시스템 구현** (v2.1 완료)
- [x] **구독 결제 연동 (TossPayments)** (v2.1 완료)
- [x] **하이브리드 신뢰 모델 UI** (v2.1 완료)
- [ ] Premium 전환 퍼널 최적화
- [ ] 구독 결제 실패 재시도 시스템
- [ ] Premium 사용자 전용 지원 채널
- [x] 수업 완료 양측 확인 기능
- [x] 노쇼 이의제기 시스템 (24h)
- [x] 분쟁 처리 관리자 대시보드
- [x] 환불 정책 고지 UI
- [x] 정산 내역 화면
- [x] 온보딩 플로우

### 17.3 Phase 2: Growth
**기간**: 2026.03 - 2026.06
- [ ] 모바일 앱 출시 (React Native)
- [ ] 실시간 알림 시스템
- [ ] **Premium 전용 기능 확대** (v2.1)
  - 긴급 매칭 서비스
  - 프로필 부스트
  - 상세 분석 리포트
- [ ] **Premium 가격 A/B 테스트** (v2.1)
- [ ] **연간 구독 옵션 (20% 할인)** (v2.1)
- [ ] Trust Score 시스템 고도화
- [ ] 이탈 추적 자동화 (Churn Signal)
- [ ] 퍼널 분석 (Mixpanel)

### 17.4 Phase 3: Scale
**기간**: 2026.07 - 2026.12
- [ ] 지역 확장 (7대 광역시)
- [ ] AI 매칭 고도화
- [ ] 강사 교육 프로그램
- [ ] B2B 엔터프라이즈
- [ ] 자격증 자동 검증 (발급기관 API)

### 17.5 Phase 4: Platform
**기간**: 2027.01 - 2027.06
- [ ] 오픈 API 제공
- [ ] 써드파티 연동
- [ ] 국제화 (일본, 동남아)
- [ ] 데이터 분석 서비스

### 17.6 기술 부채 해결
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
| 보증금 | 신뢰 담보금 (3만원/5만원) |
| Trust Score | 신뢰도 종합 점수 (0-100) |
| 분쟁 (Dispute) | 계약 관련 양측 이견 발생 건 |
| Churn Signal | 이탈 위험 징후 지표 |
| 조용한 이탈 | 탈퇴 없이 장기 미접속 상태 |
| **Free 회원** | 보증금 기반 기본 회원 (v2.1) |
| **Premium 회원** | 월 구독 기반 프리미엄 회원 (v2.1) |
| **LTV** | Lifetime Value, 고객 생애 가치 (v2.1) |
| **ARPU** | Average Revenue Per User (v2.1) |

### B. 참고 문서
- [API Documentation](./API_SPEC.md)
- [Database Schema](./DB_SCHEMA.md)
- [Security Policy](./SECURITY.md)
- [Development Guide](./CLAUDE.md)

### C. 연락처
- Product Owner: product@StudioBridge.com
- Tech Lead: tech@StudioBridge.com
- Customer Support: support@StudioBridge.com

### D. 변경 이력
| 버전 | 날짜 | 변경 내용 |
|------|------|----------|
| 1.0.0 | 2026-02-14 | 초기 작성 (MVP) |
| 2.0.0 | 2026-02-14 | 신뢰/간결성/정확성 보완, 1인 운영 설계, 이탈 추적, 분쟁 해결, 결제 거부감 해소 전략 추가 |
| **2.1.0** | **2026-02-16** | **Premium 멤버십 추가 - 하이브리드 신뢰 모델 (Free/Premium 선택), 구독 결제, 보증금 완전 면제, 우선 노출/지원, 수수료 할인** |

---

*이 문서는 살아있는 문서로, 지속적으로 업데이트됩니다.*

**Last Updated**: 2026-02-14
**Version**: 2.0.0
**Status**: MVP Complete → 운영 준비
