'use client';

import { useAuthStore } from '@/stores/auth-store';
import { InstructorProfileForm } from '@/components/profile/instructor-profile-form';
import { StudioProfileForm } from '@/components/profile/studio-profile-form';
import { VerificationSection } from '@/components/profile/verification-section';
import { MembershipSection } from '@/components/profile/membership-section';
import { TrustScoreDetail } from '@/components/profile/trust-score-detail';
import { ProfileCompleteness } from '@/components/profile/profile-completeness';

export default function ProfilePage() {
  const { user } = useAuthStore();
  const isInstructor = user?.role === 'instructor';

  return (
    <div className="space-y-6">
      <h2 className="text-2xl font-bold">1단계: 프로필 완성</h2>

      {/* Score Row */}
      <div className="grid gap-4 md:grid-cols-2">
        <ProfileCompleteness />
        <TrustScoreDetail />
      </div>

      {/* Main Content */}
      <div className="grid gap-6 md:grid-cols-2">
        <div>
          {isInstructor ? <InstructorProfileForm /> : <StudioProfileForm />}
        </div>
        <div className="space-y-6">
          <VerificationSection />
          <MembershipSection />
        </div>
      </div>
    </div>
  );
}
