'use client';

import { useAuthStore } from '@/stores/auth-store';
import { useRouter, usePathname } from 'next/navigation';
import { useEffect } from 'react';
import { Header } from '@/components/layout/header';
import { BottomTabBar } from '@/components/layout/bottom-tab-bar';
import { VerificationRequiredScreen } from '@/components/layout/verification-required-screen';

/** Pages that bypass the verification gate */
const VERIFICATION_BYPASS_PATHS = ['/steps/profile', '/settings'];

export default function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const { isAuthenticated, isLoading, user } = useAuthStore();
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.push('/login');
    }
  }, [isAuthenticated, isLoading, router]);

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <div className="mx-auto h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent" />
          <p className="mt-4 text-sm text-muted-foreground">로딩 중...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated || !user) {
    return null;
  }

  // Verification gate: block unverified users except on bypass pages
  const isBypassPath = VERIFICATION_BYPASS_PATHS.some((p) => pathname.startsWith(p));

  if (!isBypassPath) {
    const isInstructor = user.role === 'instructor';
    const needsVerification = isInstructor
      ? !user.phone_verified && !user.identity_verified
      : !user.business_verified;

    if (needsVerification) {
      return (
        <div className="min-h-screen bg-background">
          <Header />
          <VerificationRequiredScreen role={isInstructor ? 'instructor' : 'studio'} />
          <BottomTabBar />
        </div>
      );
    }
  }

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="mx-auto max-w-4xl px-4 pb-24 pt-6">{children}</main>
      <BottomTabBar />
    </div>
  );
}
