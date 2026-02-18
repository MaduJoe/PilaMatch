# Product Requirements Document (PRD)
# PilaMatch - 필라테스/요가 강사 매칭 플랫폼

**Version**: 2.2.0
**작성일**: 2026-02-18
**상태**: Phase 2 구현 완료 → 운영 준비

> **v2.2 변경 요약**: 보증금 시스템 완전 제거, Trust Score 재설계, 프로필 완성도 게이트 신설, 긴급 매칭/지원서 템플릿 구현 완료, 프론트엔드 모듈화 완료

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
18. [CHANGELOG](#18-changelog)

---

## 1. Executive Summary

### 1.1 제품 비전
> "작지만 믿을 수 있는 플랫폼" - 신뢰 기반의 필라테스/요가 강사-스튜디오 매칭 서비스

### 1.2 핵심 가치
- **신뢰 (Trust)**: 검증된 사용자, 안전한 거래, 투명한 시스템, 공정한 분쟁 해결
- **간결함 (Simplicity)**: 핵심 기능에 집중, 직관적인 UX, 최소 스텝 원칙
- **정확성 (Accuracy)**: 계약/결제 프로세스의 오류 없는 동작, 정책의 명확한 고지
- **안정성 (Stability)**: 서비스 가용성 99.9% 이상 목표

### 1.3 설계 원칙 (v2.2 개정)

#### 간결성 원칙
하나의 앱 안에서 모든 프로세스를 유저가 간편하게 파악 가능해야 한다.
- UI/UX가 누구에게나 직관적이고 쉬워야 한다
- 화면의 이동이나 움직임을 최소화할 것 (등록, 취소 등 과정이 최소 스텝으로 진행)

#### 정확성 원칙
계약이나 결제 관련 프로세스가 오류 없이 정교하게 동작해야 한다.
- 노쇼 발생 시 책임 소재가 명확하고, 노쇼 강사 또한 불만이 없어야 한다
- 취소/환불 정책에 대해 스튜디오, 강사 모두 명확히 인지할 수 있어야 한다

#### **구독 기반 신뢰 원칙 (v2.2 전면 개정)** [v2.2]
~~하이브리드 신뢰 원칙 (v2.1): 사용자가 보증금 또는 구독 중 선택~~

**보증금 시스템을 완전 제거하고, 프로필 완성도와 Trust Score 기반의 신뢰 체계로 전환.**
- **Free**: 프로필 완성도 70% 이상 달성 시 서비스 이용 가능 (보증금 없음)
- **Premium**: 월 9,900원 구독, 추가 혜택 제공 (수수료 3%, 무제한 지원, 프로필 부스트 등)
- Premium = 더 빠른 계약 성공 도구, Free = 기본 매칭 서비스

> **전환 배경**: 보증금은 가입 전환율을 저해하고 법적 리스크(약관규제법)를 야기하며, 1인 운영자에게 과도한 CS/에스크로 관리 부담을 발생시킴. 프로필 완성도 게이트로 대체하여 금전적 진입장벽을 정보 진입장벽으로 전환.

### 1.4 제품 개요
PilaMatch는 필라테스/요가 강사와 스튜디오를 연결하는 B2B 매칭 플랫폼으로, Trust Score와 프로필 완성도 기반의 신뢰 체계 및 Premium 구독을 통해 검증된 사용자 간의 안전한 거래를 보장하는 서비스입니다.

### 1.5 Premium 멤버십 가치 제안 (v2.2 개정) [v2.2]
"월 9,900원으로 더 빠른 계약 성공을 경험하세요"

**핵심 차별화**:
- **수수료 40% 할인**: Free 5% → Premium 3%
- **무제한 동시 지원**: Free 최대 5개 동시 지원 제한
- **30% 프로필 부스트**: 매칭 점수 1.3배 상승, 상단 노출
- **긴급 매칭 독점 접근**: 24시간 내 공고 (Emergency Jobs)
- **지원서 템플릿**: 최대 10개, 자동 완성 지원
- **Trust Score +10 보너스**

> **마케팅 메시지**: "한 번의 계약으로 Premium 2개월 비용 회수 / Premium 강사는 평균 3일 더 빨리 계약을 받습니다"

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
| 인력 소개소 | 오프라인 신뢰 | 높은 수수료(20-30%) | 낮은 수수료(3-5%) |

---

## 3. 솔루션 개요

### 3.1 핵심 솔루션

#### 신뢰 시스템 (Trust System) [v2.2 개정]

```
┌─────────────────────────────────────────┐
│         5-Layer Trust System            │
├─────────────────────────────────────────┤
│ 1. Identity Verification (본인인증)     │
│    - SMS OTP (6자리)                    │
│    - 사업자등록번호 검증                 │
│    - 자격증 검증 (사진 업로드 + 확인)   │
├─────────────────────────────────────────┤
│ 2. Profile Completeness (프로필 완성도) │ ← [v2.2 신규 - 보증금 대체]
│    - 강사/스튜디오별 완성도 계산 (0-100%)│
│    - 70% 이상: 서비스 이용 가능         │
│    - 90% 이상: 우선 매칭 혜택           │
│                                         │
│    [DEPRECATED v2.2: Deposit System]    │
│    ~~2. Deposit System (보증금)~~       │
│    ~~- 50,000원 예치~~                  │
│    ~~- 노쇼 시 30,000원 차감~~         │
├─────────────────────────────────────────┤
│ 3. Escrow Payment (에스크로)            │
│    - 플랫폼 보관 → 양측 완료 확인 후 지급│
│    - 자동 환불/정산 시스템               │
├─────────────────────────────────────────┤
│ 4. Penalty System (패널티)              │
│    - 노쇼 신고 → 24h 이의제기 → 확정    │
│    - 3회 누적 시 계정 정지               │
│    - [v2.2] 금전적 차감 없음 (정지만)   │
│    - 신고/차단 시스템                    │
├─────────────────────────────────────────┤
│ 5. Trust Score (신뢰 점수)              │ ← [v2.2 재설계]
│    - 4개 컴포넌트 기반 0-100점          │
│    - 4개 레벨: 신진/인증/전문/마스터    │
└─────────────────────────────────────────┘
```

### 3.2 매칭 알고리즘 (v2.2 개정)
4개 요소 가중치 기반 점수 계산 (0-100점):
- **지역 적합도**: 30% - 활동 가능 지역 매칭
- **경력 충족도**: 25% - 요구 경력 대비 실제 경력
- **자격증 보유**: 25% - 필수 자격증 매칭률
- **희망 시급**: 20% - 시급 범위 적합도

**Premium 부스트 적용** [v2.2]: Premium 회원 점수 × 1.3 (최대 100점 상한)

### 3.3 제공 가치
| 대상 | 제공 가치 |
|------|----------|
| **스튜디오** | 검증된 강사 풀, 노쇼 패널티 시스템, 간편한 관리, 투명한 정산 |
| **강사** | 안정적인 일자리, 빠른 정산, 공정한 평가, 이의제기 권리 |
| **플랫폼** | 거래 수수료 (Free 5% / Premium 3%), Premium 구독료 |

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

### 4.4 수익 모델 (v2.2 개정) [v2.2]

#### 4.4.1 구독 기반 수익 모델

| 구분 | Free (기본) | Premium (월 9,900원) |
|------|------------|---------------------|
| **진입 조건** | **프로필 완성도 70%** | 월 구독 결제 |
| ~~**신뢰 방식**~~ | ~~보증금 50,000원~~ | ~~보증금 완전 면제~~ |
| **거래 수수료** | 5% | **3% (40% 할인)** |
| **동시 지원 수** | **최대 5개** | **무제한** |
| **매칭 노출** | 기본 노출 | **우선 노출 (+30% 부스트)** |
| **긴급 매칭** | 미제공 | **제공 (24h 내 공고)** |
| **지원서 템플릿** | 미제공 | **최대 10개** |
| **고객 지원** | 이메일 24h | **우선 응답 1h** |
| **Trust Score** | 기본 | **+10 보너스** |

#### 4.4.2 Premium 전환율 목표
- 전체 가입자 대비 Premium: **15-20%**
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
수수료 부담: 강사 정산 시 차감 (스튜디오 지불 금액에서 공제 후 강사 지급)
과금 시점: 수업 완료 확인 후 정산 시에만 발생
취소된 계약: 수수료 미발생
표시 방법: 계약 확인 화면에 "예상 정산액" 항상 표시

  예) 시급 80,000원 × 8시간 = 640,000원
      플랫폼 수수료 (Free 5%): -32,000원
      예상 정산액: 608,000원

      플랫폼 수수료 (Premium 3%): -19,200원
      예상 정산액: 620,800원
```

### 4.5 가입 전환율 개선 전략 (v2.2 개정) [v2.2]

#### 4.5.1 프로필 완성도 게이트 (보증금 진입장벽 대체)
```
기존 (v2.1): 가입 → 프로필 작성 → 공고 탐색 → [지원하기] 클릭 시 보증금 요구
변경 (v2.2): 가입 → 프로필 작성 (70% 완성 요구) → 공고 탐색 → 지원

원칙: 금전적 진입장벽 → 정보 완성도 진입장벽
      "70% 달성하면 무료로 서비스 이용 가능" 긍정적 동기 부여
```

#### 4.5.2 ~~얼리버드 프로그램 (보증금 기반, DEPRECATED v2.2)~~
```
[DEPRECATED v2.2]
~~런칭 후 3개월간:~~
  ~~- 보증금: 50,000원 → 30,000원 (40% 할인)~~
  ~~- 첫 거래 수수료: 5% → 0% (면제)~~
  ~~- 프로필에 "얼리버드 뱃지" 부여~~
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
- **[v2.2]** 가입 시 보증금 요구 없음 (구 v2.1 하이브리드 모델 화면 제거)

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

#### 6.1.3 자격증 검증
```
자격증 검증 프로세스:
1. 강사가 자격증 사진/PDF 업로드
2. 운영자 수동 확인 (발급기관, 이름, 유효기간 대조)
3. 검증 완료 시 프로필에 ✓ 마크 부여
4. 유효기간 만료 30일 전 → 자동 알림 발송

향후 자동화 (Phase 3):
- 주요 발급기관(BASI, STOTT, PMA 등) API 연동 자동 검증
```

#### 6.1.4 프로필 완성도 게이트 (v2.2 신규, 보증금 대체) [v2.2]

```
완성도 계산 (강사):
  - 기본 정보 (표시명, 카테고리, 경력): 필수
  - 지역 설정: 필수
  - 본인인증 (SMS OTP): 필수
  - 프로필 사진: 선택
  - 자격증 등록: 선택
  - 자기소개 (bio): 선택

완성도 계산 (스튜디오):
  - 기본 정보 (상호, 사업자번호, 주소): 필수
  - 사업자 인증: 필수
  - 운영 시간: 필수
  - 시설 정보: 선택

게이트 기준:
  - 70% 미만: 서비스 이용 불가 (공고 탐색만 가능)
  - 70% 이상: 지원/공고 등록 가능
  - 90% 이상: 우선 매칭 혜택

API 엔드포인트:
  GET  /api/v1/profiles/completeness
  GET  /api/v1/profiles/completeness/check/{action}
```

#### ~~6.1.4 보증금 시스템 (DEPRECATED v2.2)~~ [v2.2]
```
[DEPRECATED v2.2 - 2026-02-18 제거]
~~- 기본 보증금: 30,000원 (런칭 프로모션) / 정상가 50,000원~~
~~- 충전 방법: TossPayments 결제~~
~~- 결제 시점: 첫 지원(강사) 또는 첫 오퍼 발송(스튜디오) 시~~
~~- 차감 규칙: 노쇼 확정 시 30,000원~~
~~- 환불 조건: 서비스 탈퇴 시, 패널티 없을 때~~

마이그레이션 상태:
  - DB 컬럼(deposit_balance, deposit_required) DEPRECATED 마킹 유지 (데이터 보존)
  - deposit_required = 0 설정 완료 (Migration 006)
  - 모든 보증금 관련 UI/API 비활성화 완료
```

#### 6.1.5 온보딩 플로우 (v2.2 개정) [v2.2]
```
강사 온보딩 (3화면):
  화면 1: "프로필을 완성하면 매칭이 시작돼요"
          → 이름, 카테고리, 경력, 지역 입력 (한 화면)
  화면 2: "자격증을 등록하면 Trust Score가 올라가요"
          → 자격증 사진 업로드 (건너뛰기 가능)
  화면 3: "준비 완료! 70% 완성 시 지원 가능"
          → 프로필 완성도 바 표시 후 대시보드 이동

스튜디오 온보딩 (3화면):
  화면 1: "스튜디오 정보를 등록하세요"
          → 상호, 주소, 사업자번호 입력
  화면 2: "어떤 강사가 필요하세요?"
          → 첫 구인공고 작성 유도 (건너뛰기 가능)
  화면 3: "준비 완료! 매칭을 시작하세요"
          → 대시보드로 이동

[v2.2] 보증금 안내 화면 완전 제거
[v2.2] 하이브리드 신뢰 모델 선택 화면(Free/Premium) 제거
```

#### 6.1.6 탈퇴 처리
```
탈퇴 전 확인:
  - 진행 중(CONFIRMED, IN_PROGRESS) 계약이 있으면 → 탈퇴 불가
  - 미정산 금액이 있으면 → 정산 완료 후 탈퇴 가능
  - [v2.2] 보증금 환불 프로세스 제거

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
  "trust_score": 87,
  "trust_level": "전문",
  "profile_completeness": 92
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
  "trust_score": 92,
  "trust_level": "마스터",
  "profile_completeness": 88
}
```

#### 6.2.3 Trust Score 시스템 (v2.2 전면 재설계) [v2.2]

```
Trust Score 구성 (0-100점):

컴포넌트                  가중치   최대 점수
─────────────────────────────────────────
본인인증 완료              20점    20
프로필 완성도              15점    15
활동 지표 (계약 완료 횟수) 20점    20
리뷰 평균 점수             15점    15
멤버십 등급 (Premium)      10점    10
커뮤니티 스탠딩            20점    20
페널티 차감               -최대 30점

[DEPRECATED v2.2: 보증금 예치 +10점 항목 제거]

신뢰 레벨:
  신진 (Bronze):  0-39점
  인증 (Silver): 40-59점
  전문 (Gold):   60-79점
  마스터 (Platinum): 80-100점

표시 방식:
  - 프로필 카드에 Trust Score 레벨 뱃지
  - 마스터: 🟢 / 전문: 🔵 / 인증: 🟡 / 신진: 표시 안 함
  - 매칭 리스트에서 Trust Score 정렬 옵션

API 엔드포인트:
  GET  /api/v1/trust-score              - 내 점수 상세 조회
  GET  /api/v1/trust-score/display      - 간략 표시용
  GET  /api/v1/trust-score/user/{id}    - 타인 공개 점수 조회
  POST /api/v1/trust-score/refresh      - 수동 재계산 요청
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

[v2.2] 긴급 매칭 표시:
- 수업 시작 24시간 이내 공고: is_urgent = true
- Premium 회원만 열람/지원 가능
```

#### 6.3.2 매칭 시스템 (v2.2 개정) [v2.2]
```python
# 기본 매칭 점수 계산
매칭_점수 = (
    지역_점수 * 0.30 +
    경력_점수 * 0.25 +
    자격증_점수 * 0.25 +
    시급_점수 * 0.20
)

# Premium 부스트 적용 (v2.2 신규)
if is_premium:
    매칭_점수 = min(100, round(매칭_점수 * 1.3))

매칭 라벨:
- 90-100점: Perfect Match
- 75-89점: Great Match
- 60-74점: Good Match
- 40-59점: Fair Match
- 0-39점: Low Match

정렬 순서:
1. Premium 회원 공고/지원서 우선 배치
2. 동일 그룹 내 매칭 점수 순
```

#### 6.3.3 지원서 (Application) (v2.2 개정) [v2.2]
- **동시 지원 제한**: Free 최대 5개 PENDING 상태 지원, Premium 무제한
- **커버레터**: 선택사항, 최대 500자
- **자동 첨부**: 강사 프로필 정보
- **상태 관리**: PENDING → ACCEPTED/REJECTED → WITHDRAWN
- **[v2.2]** ~~보증금 체크 제거~~ → 프로필 완성도 70% 이상 체크로 대체
- **[v2.2]** APPLICATION_LIMIT 에러: Free 5개 초과 시 반환, upgrade prompt 표시

#### 6.3.4 지원서 템플릿 (Application Template) - Premium 전용 [v2.2 신규]
```
기능:
  - 자주 쓰는 커버레터 템플릿 저장
  - 최대 10개 보유 (Premium 전용)
  - 기본 템플릿 1개 설정
  - 공고 유형별 사용 제안
  - 사용 횟수 추적

API 엔드포인트:
  GET    /api/v1/application-templates           - 템플릿 목록
  POST   /api/v1/application-templates           - 템플릿 생성
  PUT    /api/v1/application-templates/{id}      - 템플릿 수정
  DELETE /api/v1/application-templates/{id}      - 템플릿 삭제
  GET    /api/v1/application-templates/suggestions - 공고 유형별 추천
  POST   /api/v1/application-templates/{id}/use   - 템플릿 사용 기록

데이터:
  name       VARCHAR(100)  - 템플릿 이름
  content    TEXT          - 내용
  is_default BOOLEAN       - 기본 템플릿 여부
  usage_count INTEGER      - 사용 횟수
```

#### 6.3.5 긴급 매칭 (Emergency Matching) - Premium 전용 [v2.2 신규]
```
정의: 수업 시작 24시간 이내에 등록된 공고
대상: Premium 회원만 열람 및 지원 가능
표시: 🚨 긴급 뱃지
필터: Free 회원 목록에서 완전 비표시

비즈니스 가치:
  - 스튜디오: 급한 대체 강사 수요 충족
  - Premium 강사: 경쟁이 적은 긴급 공고 독점 접근
  - 플랫폼: Premium 전환 유인 강화
```

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

#### 6.4.3 수업 완료 상호 확인
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
  - 한쪽만 확인, 24시간 경과 → 자동 완료 처리
  - 양측 미확인, 48시간 경과 → 자동 완료 처리
  - 완료 거부 (문제 발생) → DISPUTED → 분쟁 해결 프로세스 진입
```

#### 6.4.4 계약 이벤트 로그
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
5. 양측 완료 확인
   ↓
6. 에스크로 RELEASED
   ↓
7. 강사 정산 (Free: 95%, Premium: 97%)  ← [v2.2 차등 수수료]
```

#### 6.5.2 차등 수수료 구조 (v2.2 신규) [v2.2]
```
적용 시점: 계약 완료 확인 시 (양방향 확인, 자동 완료 포함)

멤버십 등급별 수수료:
  Free 회원: 5% (강사 정산액 = 계약금액 × 95%)
  Premium 회원: 3% (강사 정산액 = 계약금액 × 97%)

구현 위치: /backend/app/services/contract.py::_get_fee_rate()

예시:
  계약 금액 640,000원 기준
  - Free: 수수료 32,000원, 정산 608,000원
  - Premium: 수수료 19,200원, 정산 620,800원
  - Premium 절감액: 12,800원/건 → 약 8개월 구독료 회수 가능
```

#### 6.5.3 환불 정책
| 시점 | 환불 비율 | 조건 |
|------|----------|------|
| 수업 24시간 전 | 100% | 무조건 |
| 수업 24시간 이내 | 70% | 강사 동의 필요 |
| 수업 시작 후 | 0% | 환불 불가 |
| 노쇼 (강사) | 100% | 자동 처리 |

> **[v2.2 변경]**: 노쇼 시 보증금 차감(30,000원) 없음. 스튜디오에 계약금 100% 환불 및 강사 계정 노쇼 카운트 증가(3회 시 정지).

#### 6.5.4 정산 내역 투명성
```
강사 정산 내역 (계약 건별):
  - 계약번호: #CTR-20260220-001
  - 스튜디오: 강남 필라테스
  - 수업일시: 2026-02-20 10:00-18:00 (8시간)
  - 시급: 80,000원
  - 총 금액: 640,000원
  - 플랫폼 수수료 (Free 5% / Premium 3%): -32,000원 / -19,200원
  - 정산 금액: 608,000원 / 620,800원
  - 정산 상태: 정산 완료 (2026-02-22)
```

### 6.6 신뢰 시스템

#### 6.6.1 노쇼 판정 (v2.2 개정) [v2.2]
```
프로세스:
1. 스튜디오가 "노쇼 신고" 접수
2. 강사에게 즉시 알림
3. 24시간 이의제기 기간 부여
   - 이의제기 없음 → 패널티 자동 확정:
     · no_show_count += 1
     · [v2.2] 보증금 차감 없음 (deposit_balance 변경 안 함)
     · if no_show_count >= 3: is_suspended = True
     · 스튜디오 전액 환불
   - 이의제기 있음 → 분쟁 해결 프로세스 진입
```

#### 6.6.2 분쟁 해결 프로세스
```
1단계: 자동 조정 (즉시)
  · 이의제기 없으면 → 자동 확정
  · 이의제기 있으면 → 2단계 이관

2단계: 증거 기반 심사 (48시간 이내)
  · 자동 분쟁 리포트 생성 (채팅, 접속로그, 리마인더 확인)
  · 관리자 판정: [강사측 확정] [스튜디오측 확정] [양측 부분책임]

3단계: 최종 이의 (7일 이내)
  · 1회 한정 최종 이의, 운영자 최종 판정
```

#### 6.6.3 리뷰 시스템
- **작성 권한**: 계약 완료 후 7일 이내
- **평가 항목**: 전문성 / 시간 준수 / 커뮤니케이션 / 종합 만족도 (1-5점)
- **리뷰 공개**: 양방향 작성 완료 후

### 6.7 커뮤니케이션

#### 6.7.1 실시간 채팅
- **채팅방 생성**: 계약 체결 시 자동
- **참여자**: 강사, 스튜디오
- **메시지 유형**: 텍스트, 시스템 알림

#### 6.7.2 알림 시스템
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
| **[v2.2] APPLICATION_LIMIT 도달** | 강사 (Free) | 인앱 |
| **[v2.2] 긴급 매칭 등록** | Premium 강사 | 인앱, SMS |

### 6.8 법적 기반

#### 6.8.1 필수 약관
```
가입 시 동의 필수:
  - 서비스 이용약관
  - 개인정보 수집 및 이용 동의
  - 제3자 정보 제공 동의 (결제사, SMS 발송 등)
  - 전자금융거래 이용약관 (에스크로 관련)

선택 동의:
  - 마케팅 수신 동의 (이메일, SMS)

[v2.2] 보증금 관련 약관 항목 제거 (법적 리스크 해소)
```

---

## 7. 비기능 요구사항

### 7.1 성능 요구사항
| 항목 | 목표 | 측정 방법 |
|------|------|----------|
| 응답 시간 | < 200ms (P95) | APM 모니터링 |
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
│  Auth  │ Matching │ Contract │ Payment   │
│  Trust │ Dispute  │ Template │ Premium   │
│  Profile Completeness │ Analytics        │
└──────────────────────────────────────────┘
                      │
┌─────────────────────┴───────────────────┐
│            Data Layer                    │
│  PostgreSQL │ Redis │ S3                 │
└─────────────────────────────────────────┘
```

### 8.2 기술 스택
| Layer | Technology | Version | Purpose |
|-------|------------|---------|---------|
| **Language** | Python | 3.11+ | 비동기 성능, 타입 힌트 |
| **Backend** | FastAPI | 0.109+ | REST API |
| **ORM** | SQLAlchemy | 2.0+ | 비동기 DB 작업 |
| **Database** | PostgreSQL | 15+ | ACID, JSON 지원 |
| **Cache** | Redis | 7+ | 세션, OTP 저장 |
| **Container** | Docker | 24+ | 컨테이너화 |
| **Frontend** | Streamlit | 1.30+ | MVP UI (모듈화 완료) |
| **Package** | uv | latest | 패키지 관리 |

### 8.3 프론트엔드 모듈화 구조 (v2.2 신규) [v2.2]
```
frontend/
├── app.py                  # 메인 진입점 (라우팅)
├── api_client.py           # HTTP 클라이언트 래퍼
├── pages/
│   ├── step1_profile.py    # 프로필 관리 (완성도 표시, 보증금 섹션 제거)
│   ├── step2_jobs.py       # 공고/지원 (동시 지원 수, Premium 배지)
│   ├── step3_contracts.py  # 계약 관리
│   └── step4_reviews.py    # 리뷰 관리
└── components/             # 공통 UI 컴포넌트
```

---

## 9. 데이터베이스 설계

### 9.1 주요 테이블

#### users (v2.2 개정)
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

    -- Trust System (v2.2 재설계)
    trust_score INTEGER DEFAULT 40,         -- [v2.2] 기본값 40 (신진 레벨 하한)
    trust_level VARCHAR(20) DEFAULT '신진', -- [v2.2] 신진/인증/전문/마스터

    -- Deposit (DEPRECATED v2.2)
    deposit_balance NUMERIC(10,2) DEFAULT 0,   -- DEPRECATED: 사용 안 함
    deposit_required NUMERIC(10,2) DEFAULT 0,  -- DEPRECATED: 항상 0

    -- Penalty
    no_show_count INTEGER DEFAULT 0,
    is_suspended BOOLEAN DEFAULT FALSE,

    -- Premium Membership
    membership_tier VARCHAR(20) DEFAULT 'free',  -- 'free' | 'premium'

    -- Activity Tracking
    last_active_at TIMESTAMP,
    onboarding_completed BOOLEAN DEFAULT FALSE,

    -- Timestamps
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

-- [v2.2] 신규 인덱스
CREATE INDEX ix_users_trust_score ON users(trust_score);
CREATE INDEX ix_users_trust_level ON users(trust_level);
```

#### contracts (v2.2 개정)
```sql
CREATE TABLE contracts (
    id VARCHAR(36) PRIMARY KEY,
    offer_id VARCHAR(36) REFERENCES offers(id),
    studio_id VARCHAR(36) REFERENCES studio_profiles(id),
    instructor_id VARCHAR(36) REFERENCES instructor_profiles(id),

    status VARCHAR(20) NOT NULL,
    date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    hourly_rate NUMERIC(10,2) NOT NULL,
    total_amount NUMERIC(10,2) NOT NULL,
    platform_fee NUMERIC(10,2) DEFAULT 0,
    platform_fee_rate NUMERIC(5,4) DEFAULT 0.05, -- [v2.2] 수수료율 기록 (0.05 or 0.03)
    settlement_amount NUMERIC(10,2) DEFAULT 0,

    -- Completion confirmation
    studio_confirmed_at TIMESTAMP,
    instructor_confirmed_at TIMESTAMP,

    -- Policy agreement
    policy_agreed_at TIMESTAMP,
    policy_version VARCHAR(10),

    cancellation_reason TEXT,
    cancelled_by VARCHAR(36),

    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);
```

#### application_templates (v2.2 신규) [v2.2]
```sql
CREATE TABLE application_templates (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) REFERENCES users(id),
    name VARCHAR(100) NOT NULL,
    content TEXT NOT NULL,
    is_default BOOLEAN DEFAULT FALSE,
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);

CREATE INDEX idx_application_templates_user ON application_templates(user_id);
```

#### subscriptions (v2.1에서 유지)
```sql
CREATE TABLE subscriptions (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) REFERENCES users(id) UNIQUE,
    tier VARCHAR(20) DEFAULT 'premium',
    status VARCHAR(20) DEFAULT 'inactive',  -- inactive/active/cancelled/expired
    start_date TIMESTAMP,
    end_date TIMESTAMP,
    next_billing_date TIMESTAMP,
    monthly_amount NUMERIC(10,2) DEFAULT 9900,
    auto_renew BOOLEAN DEFAULT TRUE,
    cancelled_at TIMESTAMP,
    toss_billing_key VARCHAR(200),
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

#### disputes (v2.0에서 유지)
```sql
CREATE TABLE disputes (
    id VARCHAR(36) PRIMARY KEY,
    contract_id VARCHAR(36) REFERENCES contracts(id),
    reported_by VARCHAR(36) REFERENCES users(id),
    reported_against VARCHAR(36) REFERENCES users(id),
    type VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL,
    objection_deadline TIMESTAMP,
    objection_reason TEXT,
    resolution VARCHAR(20),
    resolution_reason TEXT,
    resolved_by VARCHAR(36),
    resolved_at TIMESTAMP,
    evidence_snapshot JSONB,
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL
);
```

### 9.2 마이그레이션 이력
| Migration | 내용 |
|-----------|------|
| 001 | 초기 스키마 (users, profiles, job_posts, applications) |
| 002 | 계약 이벤트 로그, 분쟁 테이블 |
| 003 | PRD v2.0 업데이트 (disputes, policy_agreements, user_churn_log) |
| 004 | Premium 구독 테이블 (subscriptions, subscription_payments, subscription_history) |
| **006** | **[v2.2] 보증금 Deprecated: deposit_balance/deposit_required 컬럼 COMMENT 추가, deposit_required=0 일괄 업데이트** |
| **007** | **[v2.2] Trust Score 필드: trust_score INTEGER DEFAULT 40, trust_level VARCHAR(20) DEFAULT '신진', 인덱스 추가** |
| **008** | **[v2.2] 지원서 템플릿 테이블: application_templates 생성** |

### 9.3 인덱스 전략
```sql
CREATE INDEX idx_job_posts_status_region ON job_posts(status, region);
CREATE INDEX idx_applications_job_instructor ON applications(job_post_id, instructor_id);
CREATE INDEX idx_contracts_status_date ON contracts(status, date);
CREATE INDEX idx_users_role_verified ON users(role, identity_verified);
CREATE INDEX idx_disputes_status ON disputes(status);
CREATE INDEX ix_users_trust_score ON users(trust_score);
CREATE INDEX ix_users_trust_level ON users(trust_level);        -- [v2.2]
CREATE INDEX idx_application_templates_user ON application_templates(user_id); -- [v2.2]
```

### 9.4 데이터 보관 정책
| 데이터 유형 | 보관 기간 | 처리 방법 |
|------------|----------|----------|
| 활성 계약 | 무제한 | - |
| 완료 계약 | 5년 | 아카이브 (전자상거래법) |
| 채팅 메시지 | 1년 | 삭제 |
| 로그 데이터 | 3개월 | S3 이동 |
| 삭제된 사용자 | 30일 | 완전 삭제 |
| 정산 기록 | 5년 | 법적 보관 |
| 약관 동의 이력 | 5년 | 법적 증빙 |
| 분쟁 기록 | 3년 | 아카이브 |
| 이탈 사유 로그 | 2년 | 분석 후 삭제 |

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

#### Profile Completeness [v2.2 신규]
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /profiles/completeness | 현재 완성도 조회 |
| GET | /profiles/completeness/check/{action} | 특정 액션 가능 여부 확인 |

#### Trust Score [v2.2 신규]
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /trust-score | 내 Trust Score 상세 |
| GET | /trust-score/display | 간략 표시용 |
| GET | /trust-score/user/{id} | 타인 공개 점수 |
| POST | /trust-score/refresh | 수동 재계산 |

#### Job Posts (v2.2 개정)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /job-posts | 공고 목록 (필터링) |
| GET | /job-posts/for-me/with-matching | 매칭 점수 포함 (Premium 부스트/긴급 필터 적용) |
| POST | /job-posts | 공고 등록 |
| GET | /job-posts/{id} | 공고 상세 |
| PUT | /job-posts/{id} | 공고 수정 |
| DELETE | /job-posts/{id} | 공고 삭제 |

#### Applications (v2.2 개정)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /job-posts/{id}/apply | 지원 (동시 지원 한도 체크) |
| GET | /job-posts/{id}/applications | 지원서 목록 (Premium 우선 정렬) |
| PUT | /applications/{id} | 지원서 수정 |
| DELETE | /applications/{id} | 지원 취소 |

#### Application Templates [v2.2 신규]
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /application-templates | 템플릿 목록 |
| POST | /application-templates | 템플릿 생성 |
| PUT | /application-templates/{id} | 템플릿 수정 |
| DELETE | /application-templates/{id} | 템플릿 삭제 |
| GET | /application-templates/suggestions | 공고 유형별 추천 |
| POST | /application-templates/{id}/use | 템플릿 사용 기록 |

#### Contracts (v2.2 개정)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /contracts/from-offer/{id} | 계약 생성 |
| GET | /contracts/me | 내 계약 목록 |
| POST | /contracts/{id}/set-in-progress | 진행 시작 |
| POST | /contracts/{id}/confirm-completion | 완료 확인 (차등 수수료 적용) |
| POST | /contracts/{id}/reject-completion | 완료 거부 → 분쟁 |
| POST | /contracts/{id}/cancel | 취소 |
| POST | /contracts/{id}/report-no-show | 노쇼 신고 |
| GET | /contracts/{id}/timeline | 진행 타임라인 |

#### Subscriptions
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /subscriptions/me | 내 구독 정보 |
| POST | /subscriptions/upgrade | Premium 업그레이드 시작 |
| POST | /subscriptions/confirm | 결제 확인 |
| POST | /subscriptions/cancel | 구독 취소 |
| GET | /subscriptions/history | 변경 이력 조회 |

#### Disputes
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /disputes/me | 내 분쟁 목록 |
| POST | /disputes/{id}/object | 이의제기 |
| GET | /disputes/{id}/evidence | 증거 리포트 조회 |

#### Admin
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /admin/disputes | 미처리 분쟁 목록 |
| POST | /admin/disputes/{id}/resolve | 분쟁 판정 |
| GET | /admin/churn/dormant | 이탈 위험 사용자 목록 |

### 10.3 에러 코드 (v2.2 개정) [v2.2]
| Code | HTTP Status | Description |
|------|------------|-------------|
| UNAUTHORIZED | 401 | 인증 필요 |
| FORBIDDEN | 403 | 권한 부족 |
| NOT_FOUND | 404 | 리소스 없음 |
| ALREADY_EXISTS | 409 | 중복 데이터 |
| VALIDATION_ERROR | 422 | 검증 실패 |
| ~~INSUFFICIENT_DEPOSIT~~ | ~~400~~ | ~~보증금 부족 [DEPRECATED v2.2]~~ |
| **APPLICATION_LIMIT** | **400** | **동시 지원 한도 초과 (Free 5개) [v2.2 신규]** |
| **PROFILE_INCOMPLETE** | **400** | **프로필 완성도 70% 미달 [v2.2 신규]** |
| **PREMIUM_REQUIRED** | **403** | **Premium 전용 기능 (긴급 매칭, 템플릿) [v2.2 신규]** |
| NO_SHOW_LIMIT | 403 | 노쇼 한도 초과 (3회 정지) |
| DISPUTE_PENDING | 409 | 분쟁 진행 중 |
| ACTIVE_CONTRACT_EXISTS | 400 | 진행 중 계약 있음 — 탈퇴 불가 |

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

---

## 12. 성능 요구사항

### 12.1 응답 시간 목표
| 작업 유형 | 목표 시간 | 측정 기준 |
|-----------|----------|-----------|
| 페이지 로드 | < 1초 | P95 |
| API 응답 | < 200ms | P95 |
| 검색 결과 | < 500ms | P95 |
| 매칭 계산 (부스트 포함) | < 150ms | P95 |
| 결제 처리 | < 3초 | P99 |

---

## 13. UI/UX 요구사항

### 13.1 디자인 원칙
- **Simple**: 최소한의 클릭으로 목적 달성
- **Clear**: 명확한 정보 계층구조
- **Consistent**: 일관된 디자인 패턴
- **Responsive**: 모바일 우선 설계

### 13.2 핵심 플로우 최대 스텝 제한
| 플로우 | 목표 최대 스텝 |
|--------|--------------|
| 회원가입 → 본인인증 완료 | 4 이하 |
| 구인공고 등록 | 3 이하 |
| 공고 발견 → 지원 완료 | 2 이하 |
| 수업 완료 확인 | 1 |
| 환불 요청 | 2 이하 |

### 13.3 주요 화면

#### 13.3.1 프로필 페이지 (v2.2 개정) [v2.2]
```
┌─────────────────────────────────┐
│  Trust Score: 전문 (Gold)       │
│  ████████████████░░░░░░ 72점    │
│                                 │
│  프로필 완성도: 85%             │
│  █████████████████░░░ 85%       │
│  [완성도 높이기]                 │
│                                 │
│  [DEPRECATED: 보증금 섹션 제거] │
│                                 │
│  Premium 상태: Free             │
│  [Premium으로 업그레이드]        │
└─────────────────────────────────┘
```

#### 13.3.2 공고 목록 (v2.2 개정) [v2.2]
```
┌─────────────────────────────────┐
│  지원 현황: 3/5 (Free 한도)     │
│  [더 많이 지원하려면 Premium]   │
├─────────────────────────────────┤
│  🚨 [긴급] ⭐ Premium Studio   │
│  주말 필라테스 강사 (4시간 내)  │
│  [Perfect Match 95% ↗️]         │
│  [지원하기] ← Premium만 가능    │
├─────────────────────────────────┤
│  💎 강남 필라테스 (Premium)     │
│  평일 필라테스 강사             │
│  [Great Match 82% ↗️]           │
│  [지원하기]                     │
├─────────────────────────────────┤
│  서초 요가 스튜디오             │
│  주말 요가 강사                 │
│  [Good Match 70%]               │
│  [지원하기]                     │
└─────────────────────────────────┘
```

#### 13.3.3 Premium 혜택 안내 (v2.2 개정) [v2.2]
```
┌─────────────────────────────────────┐
│  월 9,900원으로 더 빠른 계약 성공  │
├─────────────────────────────────────┤
│  ✓ 수수료 40% 할인 (5%→3%)        │
│  ✓ 무제한 동시 지원 (현재 5개 제한)│
│  ✓ 30% 프로필 부스트 (우선 노출)  │
│  ✓ 긴급 매칭 독점 접근            │
│  ✓ 지원서 템플릿 10개             │
│  ✓ Trust Score +10점 보너스       │
│                                     │
│  [Premium 시작하기 - 9,900원/월]   │
└─────────────────────────────────────┘
```

---

## 14. 운영 설계 (1인 개발자)

> 핵심 원칙: "시스템이 자동으로 처리하고, 사람은 예외만 다룬다"

### 14.1 자동화 vs 수동 개입 기준

| 상황 | 처리 방식 | 운영자 개입 |
|------|----------|-----------|
| 노쇼 신고 → 이의제기 없음 | 자동 확정 (정지 적용) | 불필요 |
| 취소/환불 요청 | 정책 기반 자동 처리 | 불필요 |
| 수업 완료 timeout (48h) | 자동 완료 처리 | 불필요 |
| 분쟁 이의제기 발생 | 증거 리포트 자동 생성 | 판정만 수동 |
| 자격증 검증 | 사진 업로드 | 확인만 수동 |
| **[v2.2] Free 5개 지원 한도 초과** | **자동 거부 + upgrade 안내** | 불필요 |
| **[v2.2] Trust Score 계산** | **이벤트 트리거 자동 재계산** | 불필요 |

### 14.2 스케줄 작업 (Celery Beat)

```python
매 시간:
  - 이의제기 마감 체크 → 자동 확정
  - 수업 완료 48시간 미확인 → 자동 완료
  - 긴급 매칭 알림 (Premium 강사)  # [v2.2]

매일 09:00:
  - 수업 리마인더 발송 (D-1)
  - 7일 미접속 사용자 → 리마인드
  - 자격증 유효기간 만료 30일 전 알림

매월 1일:
  - 월간 정산 요약 생성 (강사별)
  - 이탈 사유 통계 집계
  - Trust Score 일괄 재계산  # [v2.2]
  - Premium 구독 갱신 처리
```

### 14.3 운영 체크리스트

**Daily:**
- [ ] 서비스 가용성 확인
- [ ] 에러율 모니터링
- [ ] 미처리 분쟁 건 확인
- [ ] 자격증 검증 대기 처리
- [ ] **[v2.2] Trust Score 이상값 점검**

**Weekly:**
- [ ] 성능 메트릭 리뷰
- [ ] 보안 로그 검토
- [ ] 백업 상태 확인
- [ ] 이탈 위험 사용자 리마인드
- [ ] **[v2.2] Premium 전환율 확인**
- [ ] **[v2.2] APPLICATION_LIMIT 도달 사용자 → upgrade 전환율 확인**

**Monthly:**
- [ ] 보안 패치 적용
- [ ] 퍼널 분석 (가입→프로필 완성→첫 지원→첫 계약)
- [ ] 탈퇴 사유 통계 분석 → 개선 항목 도출
- [ ] **[v2.2] Trust Score 분포 리뷰**

---

## 15. 배포 및 인프라

### 15.1 환경 구성
| Environment | Purpose | URL |
|-------------|---------|-----|
| Development | 개발 | dev.pilamatch.com |
| Staging | 테스트 | staging.pilamatch.com |
| Production | 운영 | pilamatch.com |

### 15.2 배포 전략
```yaml
CI/CD Pipeline:
1. Code Commit
   └─→ 2. Run Tests
       └─→ 3. Build Docker Image
           └─→ 4. Push to Registry
               └─→ 5. Deploy
                   └─→ 6. Health Check
```

### 15.3 모니터링
| 도구 | 용도 | 메트릭 |
|------|------|--------|
| Prometheus | 메트릭 수집 | CPU, Memory, Requests |
| Grafana | 시각화 | 대시보드 |
| Sentry | 에러 추적 | Exception |

### 15.4 백업 및 복구
- **데이터베이스**: 일일 전체 백업, 시간별 증분 백업
- **복구 목표**: RTO 1시간, RPO 1시간

---

## 16. 성공 지표

### 16.1 비즈니스 KPI
| 지표 | 목표 (6개월) | 측정 방법 |
|------|------------|-----------|
| MAU | 5,000명 | Analytics |
| 거래 전환율 | 30% | 지원→계약 비율 |
| 월 거래액 | 1억원 | 결제 시스템 |
| 재사용률 | 60% | 코호트 분석 |
| NPS | 50+ | 설문조사 |

### 16.2 신뢰 지표 (v2.2 개정) [v2.2]
| 지표 | 목표 (6개월) | 측정 방법 |
|------|------------|-----------|
| 분쟁 발생률 | < 5% | 분쟁 건수 / 총 거래 |
| 분쟁 자동 해결률 | > 70% | 이의제기 없이 확정 비율 |
| 노쇼율 | < 3% | 노쇼 건수 / 총 계약 |
| 평균 Trust Score | 55+ | 활성 사용자 평균 |
| ~~보증금 결제 전환율~~ | ~~> 60%~~ | ~~[DEPRECATED v2.2]~~ |
| **프로필 완성도 70% 달성률** | **> 80%** | **가입 후 7일 내** |

### 16.3 Premium 멤버십 지표
| 지표 | 목표 (6개월) | 측정 방법 |
|------|------------|-----------|
| Premium 전환율 | 15-20% | Premium 가입자 / 전체 |
| APPLICATION_LIMIT → Premium 전환 | 30% | 한도 초과 → Premium 선택 |
| Premium LTV | 60,000원 | 평균 6개월 × 9,900원 |
| Premium Churn | < 10%/월 | 월 취소율 |
| 결제 성공률 | > 95% | 성공 / 전체 시도 |

---

## 17. 로드맵

### 17.1 Phase 1: MVP ✅ 완료
**기간**: 2026.01 - 2026.02
- [x] 핵심 기능 구현
- [x] 신뢰 시스템 구축 (보증금 기반)
- [x] 에스크로 결제 시스템
- [x] 계약 상태 머신
- [x] Premium 멤버십 시스템 (v2.1)

### 17.2 Phase 2: 보증금 제거 & Trust Score 재설계 ✅ 완료 [v2.2]
**기간**: 2026.02.18 완료

- [x] **보증금 시스템 완전 제거** (Migration 006)
- [x] **Trust Score 시스템 재설계** (0-100점, 4레벨)
- [x] **프로필 완성도 게이트** (70% 요구사항)
- [x] **차등 수수료 구조** (Free 5%, Premium 3%)
- [x] **동시 지원 제한** (Free 최대 5개)
- [x] **Premium 프로필 부스트** (1.3배)
- [x] **긴급 매칭** (24시간 내 공고, Premium 전용)
- [x] **지원서 템플릿** (Premium 전용, 최대 10개)
- [x] **프론트엔드 모듈화** (pages/ 구조)

### 17.3 Phase 3: Growth
**기간**: 2026.03 - 2026.06
- [ ] 모바일 앱 출시 (React Native)
- [ ] 실시간 알림 시스템 (WebSocket)
- [ ] Premium 가격 A/B 테스트
- [ ] 연간 구독 옵션 (20% 할인)
- [ ] Trust Score 자동 갱신 (이벤트 트리거)
- [ ] 이탈 추적 자동화 (Churn Signal)
- [ ] 퍼널 분석 (Mixpanel)

### 17.4 Phase 4: Scale
**기간**: 2026.07 - 2026.12
- [ ] 지역 확장 (7대 광역시)
- [ ] AI 매칭 고도화
- [ ] 자격증 자동 검증 (발급기관 API)
- [ ] 스튜디오 노쇼 패널티 시스템

### 17.5 기술 부채 해결
| 항목 | 우선순위 | 예상 일정 |
|------|---------|----------|
| 보증금 DB 컬럼 완전 제거 | Medium | Q3 2026 |
| Trust Score 자동 갱신 최적화 | High | Q2 2026 |
| 테스트 커버리지 개선 | High | Q2 2026 |
| 마이크로서비스 전환 | Low | Q3 2026 |

---

## 18. CHANGELOG

### [2.2.0] - 2026-02-18

#### Removed (제거)
- **보증금 시스템 완전 제거**: `deposit_balance`, `deposit_required` 컬럼 DEPRECATED 처리 (Migration 006)
- Free 회원 보증금 50,000원 요구사항 제거
- 하이브리드 신뢰 모델 (Free=보증금 / Premium=면제) 개념 제거
- Trust Score 산출에서 "보증금 예치 +10점" 항목 제거
- 에러 코드 `INSUFFICIENT_DEPOSIT` 비활성화
- 노쇼 패널티 시 보증금 차감(30,000원) 제거
- 온보딩 화면 내 보증금 결제 유도 UI 제거
- 마케팅 문구 "보증금 면제" 제거
- `deposit` 관련 API endpoint 비활성화 (`api_client.py`)

#### Added (추가)
- **Trust Score 시스템**: 0-100점, 4개 레벨 (신진/인증/전문/마스터) (PRD §6.2.3)
  - 서비스: `/backend/app/services/trust_score.py`
  - API: `GET /trust-score`, `GET /trust-score/display`, `POST /trust-score/refresh`
  - Migration 007: `trust_score INTEGER DEFAULT 40`, `trust_level VARCHAR(20)`
- **프로필 완성도 게이트**: 70% 이상 달성 시 서비스 이용 가능 (PRD §6.1.4)
  - 서비스: `/backend/app/services/profile_completeness.py`
  - API: `GET /profiles/completeness`, `GET /profiles/completeness/check/{action}`
  - 에러 코드 `PROFILE_INCOMPLETE` 추가
- **차등 수수료 구조**: Free 5%, Premium 3% (PRD §6.5.2)
  - 구현: `/backend/app/services/contract.py::_get_fee_rate()`
  - `contracts` 테이블 `platform_fee_rate` 컬럼 추가
- **동시 지원 제한**: Free 최대 5개, Premium 무제한 (PRD §6.3.3)
  - 구현: `/backend/app/services/application.py`
  - 에러 코드 `APPLICATION_LIMIT` 추가
- **Premium 프로필 부스트**: 1.3배 매칭 점수 상승 (PRD §3.2)
  - 구현: `/backend/app/services/matching.py::apply_premium_boost()`
  - 응답에 `original_score`, `is_boosted`, `boost_factor` 필드 추가
- **긴급 매칭 (Emergency Matching)**: 24시간 내 공고, Premium 전용 (PRD §6.3.5)
  - 구현: `/backend/app/api/v1/endpoints/job_posts.py`
  - 에러 코드 `PREMIUM_REQUIRED` 추가
- **지원서 템플릿**: Premium 전용, 최대 10개 (PRD §6.3.4)
  - 서비스: `/backend/app/services/application_template.py`
  - API: `/api/v1/application-templates/*`
  - Migration 008: `application_templates` 테이블 생성
- **프론트엔드 모듈화**: `frontend/pages/` 구조 도입 (PRD §8.3)
  - `step1_profile.py`, `step2_jobs.py`, `step3_contracts.py`, `step4_reviews.py`
  - 프로필 페이지: Trust Score 표시, 보증금 섹션 완전 제거

#### Changed (변경)
- `신뢰 원칙` 개정: "하이브리드 신뢰 모델(보증금/구독)" → "구독 기반 신뢰 모델" (PRD §1.3)
- 노쇼 패널티: 보증금 차감 없음, 카운트 증가 및 3회 시 정지만 유지 (PRD §6.6.1)
- 온보딩 플로우: 보증금 안내 → 프로필 완성도 게이트 (PRD §6.1.5)
- 매칭 리스트 정렬: Premium 공고/지원서 우선, 동일 그룹 내 점수 순 (PRD §6.3.2)
- `api_client.py`: 보증금 관련 메서드 주석 처리, Trust Score/템플릿 메서드 추가
- 서비스 Base URL: `StudioBridge.com` → `pilamatch.com` (브랜딩 통일)

#### Fixed (수정)
- Trust Score 레벨 정의 불일치 수정 (v2.1: 90/70/50 기준 → v2.2: 80/60/40 기준)
- Free 회원 Premium 전용 기능 접근 차단 검증 로직 강화

---

### [2.1.0] - 2026-02-16
- Premium 멤버십 추가 - 하이브리드 신뢰 모델 (Free/Premium 선택)
- 구독 결제 연동 (TossPayments)
- 보증금 완전 면제 (Premium 전용 혜택)
- 우선 노출/지원, 수수료 할인

### [2.0.0] - 2026-02-14
- 신뢰/간결성/정확성 원칙 보완
- 1인 운영 설계, 이탈 추적, 분쟁 해결 프로세스
- 결제 거부감 해소 전략 (보증금 진입 시점 지연)

### [1.0.0] - 2026-02-14
- 초기 MVP 작성

---

## 부록

### A. 용어 정의
| 용어 | 정의 |
|------|------|
| 노쇼 (No-show) | 예약 후 무단 불참 |
| 에스크로 (Escrow) | 제3자 예치 결제 |
| 매칭 스코어 | 적합도 점수 (0-100) |
| 오퍼 (Offer) | 스튜디오→강사 제안 |
| ~~보증금~~ | ~~신뢰 담보금 [DEPRECATED v2.2]~~ |
| Trust Score | 신뢰도 종합 점수 (0-100), 4개 레벨 |
| 신진 (Bronze) | Trust Score 0-39점 |
| 인증 (Silver) | Trust Score 40-59점 |
| 전문 (Gold) | Trust Score 60-79점 |
| 마스터 (Platinum) | Trust Score 80-100점 |
| 프로필 완성도 | 서비스 이용 진입 기준 (70% 요구) |
| 분쟁 (Dispute) | 계약 관련 양측 이견 발생 건 |
| Churn Signal | 이탈 위험 징후 지표 |
| Free 회원 | 기본 회원 (프로필 완성도 70% 이상) |
| Premium 회원 | 월 9,900원 구독 회원 |
| 긴급 매칭 | 24시간 내 공고 (Premium 전용) |
| APPLICATION_LIMIT | Free 동시 지원 5개 제한 |
| 프로필 부스트 | Premium 매칭 점수 1.3배 상승 |

### B. 참고 문서
- API 상세: `docs/API_SPEC.md`
- DB 스키마: `docs/DB_SCHEMA.md`
- 보안 정책: `docs/SECURITY.md`
- Phase 2 구현 상세: `docs/phase2_implementation_summary.md`
- 보증금 제거 논의: `docs/summary_20260218_deposit_removal.md`
- 개발 가이드: `CLAUDE.md`

### C. 구현 상태 (2026-02-18 기준)
| 기능 | 상태 | 파일 위치 |
|------|------|----------|
| 보증금 시스템 제거 | ✅ 완료 | `services/deposit.py` (deprecated) |
| Trust Score (0-100점, 4레벨) | ✅ 완료 | `services/trust_score.py` |
| 프로필 완성도 게이트 (70%) | ✅ 완료 | `services/profile_completeness.py` |
| 차등 수수료 (Free 5%, Premium 3%) | ✅ 완료 | `services/contract.py` |
| 동시 지원 제한 (Free 5개) | ✅ 완료 | `services/application.py` |
| Premium 프로필 부스트 (1.3배) | ✅ 완료 | `services/matching.py` |
| 긴급 매칭 (24h, Premium 전용) | ✅ 완료 | `endpoints/job_posts.py` |
| 지원서 템플릿 (Premium, 최대 10개) | ✅ 완료 | `services/application_template.py` |
| 프론트엔드 모듈화 (pages/) | ✅ 완료 | `frontend/pages/` |
| Trust Score 자동 갱신 (이벤트 트리거) | 🚧 진행중 | - |
| Premium 지원 우선 응답 채널 | ❌ 미구현 | - |
| 연간 구독 옵션 | ❌ 미구현 | - |

---

*이 문서는 살아있는 문서로, 지속적으로 업데이트됩니다.*

**Last Updated**: 2026-02-18
**Version**: 2.2.0
**Status**: Phase 2 구현 완료 → 운영 준비
