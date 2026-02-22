'use client';

import { useAuthStore } from '@/stores/auth-store';
import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api-client';
import { INSTRUCTOR_STEPS, STUDIO_STEPS } from '@/lib/constants';

export function useUserProgress() {
  const { user, profileId } = useAuthStore();
  const isInstructor = user?.role === 'instructor';
  const steps = isInstructor ? INSTRUCTOR_STEPS : STUDIO_STEPS;

  const { data: profileCompleteness } = useQuery({
    queryKey: ['profile', 'completeness'],
    queryFn: () => api.profileCompleteness.get(),
    enabled: !!user,
  });

  const { data: contracts } = useQuery({
    queryKey: ['contracts', 'me'],
    queryFn: () => api.contracts.getMyContracts(),
    enabled: !!user,
  });

  // Calculate current step based on progress
  let currentStep = 0; // 0-indexed

  if (profileCompleteness) {
    if (profileCompleteness.percentage >= 70) {
      currentStep = 1; // Step 2: Jobs
    }
  }

  const contractItems = contracts?.items ?? [];
  if (contractItems.length > 0) {
    const hasActive = contractItems.some((c) =>
      ['confirmed', 'in_progress', 'pending_completion'].includes(c.status),
    );
    const hasCompleted = contractItems.some((c) => c.status === 'completed');

    if (hasActive) {
      currentStep = 3; // Step 4: Contracts
    }
    if (hasCompleted) {
      currentStep = 4; // Step 5: Complete
    }
  }

  return {
    steps,
    currentStep,
    isInstructor,
    profileComplete: (profileCompleteness?.percentage ?? 0) >= 70,
  };
}
