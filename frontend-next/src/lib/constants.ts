/**
 * Constants and configuration for PilaMatch frontend
 * Ported from frontend/utils/constants.py with Next.js adaptations
 */

// ---------------------------------------------------------------------------
// Step definitions for progress tracking
// ---------------------------------------------------------------------------

export const INSTRUCTOR_STEPS = [
  { key: 'profile', label: '프로필 완성', path: '/steps/profile' },
  { key: 'find_jobs', label: '급구/대행 찾기', path: '/steps/jobs' },
  { key: 'offers', label: '지원 현황', path: '/steps/offers' },
] as const;

export const STUDIO_STEPS = [
  { key: 'profile', label: '프로필 완성', path: '/steps/profile' },
  { key: 'create_job', label: '급구 등록', path: '/steps/jobs' },
  { key: 'applicants', label: '강사 선택', path: '/steps/offers' },
] as const;

// ---------------------------------------------------------------------------
// Seoul regions with coordinates (25 districts)
// ---------------------------------------------------------------------------

export const SEOUL_REGIONS: Record<string, { lat: number; lng: number }> = {
  '강남구': { lat: 37.5172, lng: 127.0473 },
  '서초구': { lat: 37.4837, lng: 127.0324 },
  '송파구': { lat: 37.5145, lng: 127.1050 },
  '강동구': { lat: 37.5301, lng: 127.1238 },
  '마포구': { lat: 37.5664, lng: 126.9018 },
  '용산구': { lat: 37.5326, lng: 126.9908 },
  '성동구': { lat: 37.5633, lng: 127.0370 },
  '광진구': { lat: 37.5385, lng: 127.0823 },
  '동대문구': { lat: 37.5744, lng: 127.0396 },
  '중랑구': { lat: 37.6066, lng: 127.0927 },
  '성북구': { lat: 37.5894, lng: 127.0167 },
  '강북구': { lat: 37.6397, lng: 127.0252 },
  '도봉구': { lat: 37.6688, lng: 127.0471 },
  '노원구': { lat: 37.6543, lng: 127.0568 },
  '은평구': { lat: 37.6027, lng: 126.9291 },
  '서대문구': { lat: 37.5791, lng: 126.9368 },
  '종로구': { lat: 37.5735, lng: 126.9790 },
  '중구': { lat: 37.5641, lng: 126.9979 },
  '영등포구': { lat: 37.5264, lng: 126.8963 },
  '동작구': { lat: 37.5124, lng: 126.9396 },
  '관악구': { lat: 37.4784, lng: 126.9516 },
  '금천구': { lat: 37.4519, lng: 126.8958 },
  '구로구': { lat: 37.4954, lng: 126.8874 },
  '양천구': { lat: 37.5270, lng: 126.8561 },
  '강서구': { lat: 37.5509, lng: 126.8495 },
};

export const REGION_NAMES = Object.keys(SEOUL_REGIONS);

// ---------------------------------------------------------------------------
// Hourly rate presets
// ---------------------------------------------------------------------------

export const RATE_PRESETS = [
  { value: 30000, label: '3만원' },
  { value: 40000, label: '4만원' },
  { value: 50000, label: '5만원' },
  { value: 60000, label: '6만원' },
  { value: 70000, label: '7만원+' },
] as const;

// ---------------------------------------------------------------------------
// Contract terms (Korean)
// ---------------------------------------------------------------------------

// PMF pivot: Direct settlement, no escrow
// export const CONTRACT_TERMS = `
// ## 계약 조건
//
// ### 노쇼 패널티
// - 노쇼 발생 시 30,000원 패널티가 보증금에서 차감됩니다.
// - 3회 노쇼 시 계정이 정지됩니다.
//
// ### 취소 정책
// - 수업 시작 24시간 전까지 무료 취소 가능
// - 24시간 이내 취소 시 패널티가 적용될 수 있습니다.
//
// ### 결제
// - 수업 완료 후 에스크로에서 정산됩니다.
// - 플랫폼 수수료: 무료회원 5%, 프리미엄회원 3%
// `;

export const CONTRACT_TERMS = `
## 이용 조건

### 노쇼 패널티
- 3회 노쇼 시 계정이 정지됩니다.
- Tier 등급이 강등됩니다.

### 취소 정책
- 수업 시작 24시간 전까지 무료 취소 가능
- 24시간 이내 취소 시 패널티가 적용될 수 있습니다.

### 정산
- 수업료는 강사와 스튜디오 간 직접 정산합니다.
- 플랫폼은 매칭 서비스만 제공하며 결제에 개입하지 않습니다.
`;

// ---------------------------------------------------------------------------
// Categories
// ---------------------------------------------------------------------------

export const CATEGORIES = [
  { value: 'pilates', label: '필라테스' },
  { value: 'yoga', label: '요가' },
] as const;

// ---------------------------------------------------------------------------
// Job types
// ---------------------------------------------------------------------------

export const JOB_TYPES = [
  { value: 'substitute', label: '대행' },
  { value: 'regular', label: '정규' },
  { value: 'contract', label: '계약' },
] as const;

// ---------------------------------------------------------------------------
// Trust score levels (deprecated: replaced by Tier system)
// ---------------------------------------------------------------------------

// export const TRUST_LEVELS = [
//   { min: 0, max: 29, level: 'bronze', color: '#CD7F32', label: '브론즈' },
//   { min: 30, max: 59, level: 'silver', color: '#C0C0C0', label: '실버' },
//   { min: 60, max: 79, level: 'gold', color: '#FFD700', label: '골드' },
//   { min: 80, max: 100, level: 'platinum', color: '#E5E4E2', label: '플래티넘' },
// ] as const;

// ---------------------------------------------------------------------------
// PMF pivot: Premium disabled -- free-only model during validation phase
// ---------------------------------------------------------------------------

// export const PREMIUM_PRICE = 9900;
//
// export const PREMIUM_BENEFITS = {
//   instructor: [
//     { icon: 'percent', title: '수수료 40% 할인', desc: '5% -> 3%' },
//     { icon: 'rocket', title: '무제한 일일 지원', desc: '하루 5회 -> 무제한' },
//     { icon: 'trending-up', title: '매칭 점수 30% 부스트', desc: '스튜디오에게 더 높은 점수로 노출' },
//     { icon: 'trophy', title: 'Trust Score +10점', desc: '신뢰도 레벨 상승' },
//     { icon: 'file-text', title: '지원서 템플릿 10개', desc: '빠른 지원을 위한 템플릿' },
//   ],
//   studio: [
//     { icon: 'percent', title: '수수료 40% 할인', desc: '5% -> 3%' },
//     { icon: 'eye', title: '무제한 강사 프로필 열람', desc: '하루 5명 -> 무제한' },
//     { icon: 'star', title: '공고 우선 노출', desc: '강사들에게 상단 표시' },
//     { icon: 'trophy', title: 'Trust Score +10점', desc: '신뢰도 레벨 상승' },
//     { icon: 'bar-chart', title: '프리미엄 강사 우선 매칭', desc: '프리미엄 강사 우선 정렬' },
//   ],
// } as const;

// PMF pivot: Premium disabled
// export const DEPOSIT_AMOUNT = 50000;

// PMF pivot: Premium disabled
// export const FREE_DAILY_APPLICATION_LIMIT = 5;
// export const FREE_DAILY_VIEW_LIMIT = 5;
