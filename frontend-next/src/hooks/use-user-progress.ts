'use client';

import { useAuthStore } from '@/stores/auth-store';
import { useQuery } from '@tanstack/react-query';
import api from '@/lib/api-client';
import { INSTRUCTOR_STEPS, STUDIO_STEPS } from '@/lib/constants';

export function useUserProgress() {
  const { user } = useAuthStore();
  const isInstructor = user?.role === 'instructor';
  const steps = isInstructor ? INSTRUCTOR_STEPS : STUDIO_STEPS;

  const { data: profileCompleteness } = useQuery({
    queryKey: ['profile', 'completeness'],
    queryFn: () => api.profileCompleteness.get(),
    enabled: !!user,
  });

  const { data: applications } = useQuery({
    queryKey: ['my-applications'],
    queryFn: () => api.applications.getMyApplications(),
    enabled: !!user && isInstructor,
  });

  // Step 0: Profile incomplete
  // Step 1: Profile >= 70% -> find jobs / post jobs
  // Step 2: Has applied (instructor) or profile complete (studio) -> offers / applicants
  let currentStep = 0;

  if (profileCompleteness && profileCompleteness.percentage >= 70) {
    currentStep = 1;
  }

  if (currentStep >= 1) {
    if (isInstructor) {
      const appItems = applications?.items ?? [];
      if (appItems.length > 0) {
        currentStep = 2;
      }
    } else {
      // Studio: advance to Step 2 once profile is complete
      currentStep = 2;
    }
  }

  return {
    steps,
    currentStep,
    isInstructor,
    profileComplete: (profileCompleteness?.percentage ?? 0) >= 70,
  };
}
