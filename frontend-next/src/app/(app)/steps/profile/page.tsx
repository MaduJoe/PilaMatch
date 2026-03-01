'use client';

import { useAuthStore } from '@/stores/auth-store';
import { InstructorProfileForm } from '@/components/profile/instructor-profile-form';
import { StudioProfileForm } from '@/components/profile/studio-profile-form';
import { VerificationSection } from '@/components/profile/verification-section';
// PMF pivot: Premium membership hidden
// import { MembershipSection } from '@/components/profile/membership-section';
import { TrustScoreDetail } from '@/components/profile/trust-score-detail';
import { ProfileCompletenessHeader } from '@/components/profile/profile-completeness-header';

export default function ProfilePage() {
  const { user } = useAuthStore();
  const isInstructor = user?.role === 'instructor';

  return (
    <div className="space-y-6">
      <ProfileCompletenessHeader />

      <div className="grid gap-6 md:grid-cols-2">
        <div className="space-y-6">
          {isInstructor ? <InstructorProfileForm /> : <StudioProfileForm />}
          <VerificationSection />
        </div>
        <div className="space-y-6">
          <TrustScoreDetail />
          {/* PMF pivot: Premium membership hidden */}
        </div>
      </div>
    </div>
  );
}
