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

  const { data: offers } = useQuery({
    queryKey: ['my-offers'],
    queryFn: () => api.offers.getMyOffers(),
    enabled: !!user && (profileCompleteness?.percentage ?? 0) >= 70,
  });

  const { data: contracts } = useQuery({
    queryKey: ['my-contracts'],
    queryFn: () => api.contracts.getMyContracts(),
    enabled: !!user,
  });

  // Calculate current step based on progress
  // Step 0: Profile incomplete
  // Step 1: Profile >= 70% -> find jobs / post jobs
  // Step 2: Has offers (instructor) or profile complete (studio) -> offers / applicants
  // Step 3: Has active contract -> contract in progress
  // Step 4: Has completed contract -> complete / review
  let currentStep = 0;

  if (profileCompleteness) {
    if (profileCompleteness.percentage >= 70) {
      currentStep = 1; // Step 2: Jobs
    }
  }

  // Step 2: Offers / Applicants
  const offerItems = offers?.items ?? [];
  if (currentStep >= 1) {
    if (isInstructor) {
      // Instructor: advance to Step 2 when they have received at least one offer
      if (offerItems.length > 0) {
        currentStep = 2;
      }
    } else {
      // Studio: advance to Step 2 once profile is complete
      // (they can check applicants as soon as they post a job)
      currentStep = 2;
    }
  }

  // Step 3-4: Contracts
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
