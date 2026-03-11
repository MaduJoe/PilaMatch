'use client';

import { useAuthStore } from '@/stores/auth-store';
import { InstructorProfileForm } from '@/components/profile/instructor-profile-form';
import { StudioProfileForm } from '@/components/profile/studio-profile-form';
import { VerificationSection } from '@/components/profile/verification-section';
import { TrustScoreDetail } from '@/components/profile/trust-score-detail';
import { ProfileCompletenessHeader } from '@/components/profile/profile-completeness-header';

export default function ProfilePage() {
  const { user } = useAuthStore();
  const isInstructor = user?.role === 'instructor';

  return (
    <div className="space-y-4">
      <ProfileCompletenessHeader />
      {isInstructor ? <InstructorProfileForm /> : <StudioProfileForm />}
      <TrustScoreDetail />
      <VerificationSection />
    </div>
  );
}
