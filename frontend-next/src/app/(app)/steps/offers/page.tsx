'use client';

import { useAuthStore } from '@/stores/auth-store';
import { ApplicantList } from '@/components/offers/applicant-list';
import { InstructorApplicationList } from '@/components/applications/instructor-application-list';
import { Loader2 } from 'lucide-react';

// ---------------------------------------------------------------------------
// Page: Instructor sees their applications; Studio sees applicants
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
        {isInstructor ? '지원 현황' : '지원자 선택'}
      </h1>
      <p className="mt-1 text-sm text-muted-foreground">
        {isInstructor
          ? '스튜디오가 수락하면 연락처가 공개됩니다. 여러 곳에 지원할수록 빠르게 매칭됩니다.'
          : '마음에 드는 강사를 수락하면 양측 연락처가 즉시 공개됩니다.'}
      </p>

      <div className="mt-6">
        {isInstructor ? <InstructorApplicationList /> : <ApplicantList />}
      </div>
    </div>
  );
}
