'use client';

import { useQuery } from '@tanstack/react-query';
import Link from 'next/link';
import api from '@/lib/api-client';
import { useAuthStore } from '@/stores/auth-store';
import { isUserVerified } from '@/lib/utils';
import { AlertCircle, CheckCircle2, Loader2 } from 'lucide-react';

/** Missing field key → Korean display label */
const FIELD_DISPLAY_KO: Record<string, string> = {
  display_name: '활동명',
  bio: '자기소개',
  categories: '카테고리',
  experience_years: '경력',
  available_regions: '활동 가능 지역',
  phone_verified: '휴대폰 인증',
  identity_verified: '본인 인증',
  business_verified: '사업자 인증',
  business_name: '업체명',
  description: '업체 소개',
  region: '지역',
  address: '주소',
  phone: '연락처',
};

export function ProfileCompletenessHeader() {
  const user = useAuthStore((s) => s.user);
  const isInstructor = user?.role === 'instructor';

  const { data, isLoading } = useQuery({
    queryKey: ['profile', 'completeness'],
    queryFn: () => api.profileCompleteness.get(),
  });

  if (isLoading) {
    return (
      <div className="flex items-center gap-2 py-2">
        <h2 className="text-xl font-semibold">내 프로필</h2>
        <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
      </div>
    );
  }

  // Combine profile missing fields + verification missing fields
  const profileMissing = data?.missing_fields ?? [];

  const verificationMissing: string[] = [];
  if (user) {
    const phoneOk = user.phone_verified || user.identity_verified;
    if (!phoneOk) verificationMissing.push('phone_verified');
    if (user.role === 'studio' && !user.business_verified) verificationMissing.push('business_verified');
  }

  const allMissing = [...profileMissing, ...verificationMissing];
  const verified = user ? isUserVerified(user) : false;
  const isComplete = allMissing.length === 0 && verified;

  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <h2 className="text-xl font-semibold">내 프로필</h2>
        {isComplete && (
          <CheckCircle2 className="size-5 text-green-600" />
        )}
      </div>

      {allMissing.length > 0 && (
        <div className="rounded-xl border border-red-200 bg-red-50/60 p-3 dark:border-red-900/40 dark:bg-red-950/20">
          <div className="flex items-start gap-2">
            <AlertCircle className="mt-0.5 size-4 shrink-0 text-red-500" />
            <div className="space-y-1.5">
              <p className="text-sm font-medium text-red-700 dark:text-red-400">
                아래 항목을 완료해야 {isInstructor ? '지원' : '공고 등록'}이 가능합니다
              </p>
              <ul className="space-y-0.5">
                {allMissing.map((field: string) => (
                  <li key={field} className="flex items-center gap-1.5 text-sm text-red-600 dark:text-red-400">
                    <span className="size-1 shrink-0 rounded-full bg-red-400" />
                    {FIELD_DISPLAY_KO[field] ?? field}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        </div>
      )}

      {isComplete && (
        <p className="text-sm text-green-600 dark:text-green-400">
          프로필 준비 완료!{' '}
          <Link href="/steps/jobs" className="font-medium underline underline-offset-2">
            {isInstructor ? '공고 찾아보기 →' : '공고 등록하기 →'}
          </Link>
        </p>
      )}
    </div>
  );
}
