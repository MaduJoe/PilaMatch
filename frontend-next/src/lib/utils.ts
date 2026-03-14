import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

// ---------------------------------------------------------------------------
// shadcn/ui class name merge utility
// ---------------------------------------------------------------------------

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

// ---------------------------------------------------------------------------
// Currency formatting
// ---------------------------------------------------------------------------

/** Format Korean Won (e.g., 50000 -> "\\50,000") */
export function formatCurrency(amount: number): string {
  return new Intl.NumberFormat('ko-KR', {
    style: 'currency',
    currency: 'KRW',
    maximumFractionDigits: 0,
  }).format(amount);
}

/** Format short currency (e.g., 30000 -> "3만원") */
export function formatShortCurrency(amount: number): string {
  if (amount >= 10000) {
    const man = amount / 10000;
    return `${man}만원`;
  }
  return `${amount.toLocaleString('ko-KR')}원`;
}

// ---------------------------------------------------------------------------
// Date/time formatting
// ---------------------------------------------------------------------------

/** Format date to Korean locale (e.g., "2026년 2월 23일") */
export function formatDate(date: string | Date): string {
  return new Intl.DateTimeFormat('ko-KR', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  }).format(new Date(date));
}

/** Format time string to HH:MM */
export function formatTime(time: string): string {
  return time.slice(0, 5);
}

/** Format datetime to Korean locale (e.g., "2026. 2. 23. 오후 3:00") */
export function formatDateTime(date: string | Date): string {
  return new Intl.DateTimeFormat('ko-KR', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(date));
}

// ---------------------------------------------------------------------------
// Display helpers
// ---------------------------------------------------------------------------

/** Render star rating as text (e.g., 3.7 -> "★★★★☆") */
export function renderStars(rating: number): string {
  const filled = Math.round(rating);
  return '★'.repeat(filled) + '☆'.repeat(5 - filled);
}

/** Get contract status display properties */
export function getContractStatusDisplay(status: string): {
  label: string;
  color: string;
  emoji: string;
} {
  const map: Record<string, { label: string; color: string; emoji: string }> = {
    confirmed: { label: '계약 확인됨', color: 'blue', emoji: '📋' },
    in_progress: { label: '진행 중', color: 'green', emoji: '🏃' },
    pending_completion: { label: '완료 대기', color: 'yellow', emoji: '⏳' },
    completed: { label: '완료', color: 'emerald', emoji: '✅' },
    disputed: { label: '분쟁 중', color: 'red', emoji: '⚠️' },
    cancelled: { label: '취소됨', color: 'gray', emoji: '❌' },
  };
  return map[status] || { label: status, color: 'gray', emoji: '❓' };
}

/** Get offer status display properties */
export function getOfferStatusDisplay(status: string): {
  label: string;
  color: string;
} {
  const map: Record<string, { label: string; color: string }> = {
    pending: { label: '대기 중', color: 'yellow' },
    accepted: { label: '수락됨', color: 'green' },
    rejected: { label: '거절됨', color: 'red' },
    expired: { label: '만료됨', color: 'gray' },
  };
  return map[status] || { label: status, color: 'gray' };
}

/** Get application status display properties */
export function getApplicationStatusDisplay(status: string): {
  label: string;
  color: string;
} {
  const map: Record<string, { label: string; color: string }> = {
    pending: { label: '대기 중', color: 'yellow' },
    accepted: { label: '수락됨', color: 'green' },
    rejected: { label: '거절됨', color: 'red' },
    withdrawn: { label: '철회됨', color: 'gray' },
  };
  return map[status] || { label: status, color: 'gray' };
}

// ---------------------------------------------------------------------------
// User verification helpers
// ---------------------------------------------------------------------------

/** Check if a user has completed the required verification for their role */
export function isUserVerified(user: {
  role: string;
  phone_verified: boolean;
  identity_verified: boolean;
  business_verified: boolean;
}): boolean {
  const phoneOk = user.phone_verified || user.identity_verified;
  return user.role === 'instructor'
    ? phoneOk
    : phoneOk && user.business_verified;
}

// ---------------------------------------------------------------------------
// Date calculation
// ---------------------------------------------------------------------------

/** Calculate D-day from today (e.g., "D-3", "D-Day", "D+1") */
export function getDDay(dateStr: string): string {
  const target = new Date(dateStr);
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  target.setHours(0, 0, 0, 0);
  const diff = Math.ceil(
    (target.getTime() - today.getTime()) / (1000 * 60 * 60 * 24)
  );
  if (diff === 0) return 'D-Day';
  if (diff > 0) return `D-${diff}`;
  return `D+${Math.abs(diff)}`;
}

// ---------------------------------------------------------------------------
// Payment helpers
// ---------------------------------------------------------------------------

/** Check if TossPayments is in mock mode */
export function isTossPaymentsMockMode(): boolean {
  const clientKey = process.env.NEXT_PUBLIC_TOSS_CLIENT_KEY || '';
  return !clientKey || clientKey.length < 20 || clientKey.includes('xxxx');
}
