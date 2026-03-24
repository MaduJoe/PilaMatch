'use client';

import { useAuthStore } from '@/stores/auth-store';
import { useRouter, usePathname } from 'next/navigation';
import { useEffect } from 'react';
import { Header } from '@/components/layout/header';
import { BottomTabBar } from '@/components/layout/bottom-tab-bar';
import { VerificationRequiredScreen } from '@/components/layout/verification-required-screen';
import { PushNotificationProvider } from '@/components/notification/push-provider';
import { isUserVerified } from '@/lib/utils';

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
      <div className="flex min-h-screen items-center justify-center animate-fade-in">
        <div className="text-center">
          <div className="relative mx-auto size-10">
            <div className="absolute inset-0 rounded-full border-[3px] border-primary/20" />
            <div className="absolute inset-0 animate-spin rounded-full border-[3px] border-primary border-t-transparent" />
          </div>
          <p className="mt-4 font-display text-sm text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated || !user) {
    return null;
  }

  // Verification gate: block unverified users except on bypass pages
  const isBypassPath = VERIFICATION_BYPASS_PATHS.some((p) => pathname.startsWith(p));

  if (!isBypassPath && !isUserVerified(user)) {
    return (
      <div className="min-h-screen bg-background">
        <Header />
        <VerificationRequiredScreen role={user.role === 'instructor' ? 'instructor' : 'studio'} />
        <BottomTabBar />
      </div>
    );
  }

  return (
    <PushNotificationProvider>
      <div className="min-h-screen bg-background">
        <Header />
        <main className="mx-auto max-w-4xl px-4 pb-28 pt-8">{children}</main>
        <BottomTabBar />
      </div>
    </PushNotificationProvider>
  );
}
