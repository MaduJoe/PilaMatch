'use client';

import { useAuthStore } from '@/stores/auth-store';
import { OfferList } from '@/components/offers/offer-list';
import { ApplicantList } from '@/components/offers/applicant-list';
import { Loader2 } from 'lucide-react';

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function OffersPage() {
  const user = useAuthStore((s) => s.user);
  const isLoading = useAuthStore((s) => s.isLoading);

  // Loading state while auth initialises
  if (isLoading || !user) {
    return (
      <div className="flex items-center justify-center py-20" role="status">
        <Loader2 className="mr-2 size-6 animate-spin" aria-hidden="true" />
        <span className="text-sm text-muted-foreground">로딩 중...</span>
      </div>
    );
  }

  const isInstructor = user.role === 'instructor';

  return (
    <div className="mx-auto max-w-4xl p-6">
      <h1 className="text-2xl font-bold">
        {isInstructor ? '3단계: 오퍼 확인' : '3단계: 지원자 수락'}
      </h1>
      <p className="mt-1 text-sm text-muted-foreground">
        {isInstructor
          ? '스튜디오에서 보낸 오퍼를 확인하고 수락하세요.'
          : '공고에 지원한 강사를 확인하고 수락하세요. 수락 시 양측 연락처가 공개됩니다.'}
      </p>

      <div className="mt-6">
        {isInstructor ? <OfferList /> : <ApplicantList />}
      </div>
    </div>
  );
}
