'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuthStore } from '@/stores/auth-store';
import { Search, ClipboardList, User, Megaphone, Users, LayoutDashboard } from 'lucide-react';
import { cn, isUserVerified } from '@/lib/utils';

const INSTRUCTOR_TABS = [
  { key: 'dashboard', label: 'Home', icon: LayoutDashboard, path: '/dashboard' },
  { key: 'jobs', label: 'Find', icon: Search, path: '/steps/jobs' },
  { key: 'offers', label: 'Applied', icon: ClipboardList, path: '/steps/offers' },
  { key: 'profile', label: 'Profile', icon: User, path: '/steps/profile' },
] as const;

const STUDIO_TABS = [
  { key: 'dashboard', label: 'Home', icon: LayoutDashboard, path: '/dashboard' },
  { key: 'jobs', label: 'Posts', icon: Megaphone, path: '/steps/jobs' },
  { key: 'offers', label: 'Applicants', icon: Users, path: '/steps/offers' },
  { key: 'profile', label: 'Profile', icon: User, path: '/steps/profile' },
] as const;

export function BottomTabBar() {
  const pathname = usePathname();
  const user = useAuthStore((s) => s.user);

  if (!user) return null;

  const tabs = user.role === 'instructor' ? INSTRUCTOR_TABS : STUDIO_TABS;
  const isVerified = isUserVerified(user);

  return (
    <nav
      className="fixed bottom-0 left-0 right-0 z-40 border-t border-border/50 bg-background/90 backdrop-blur-xl supports-[backdrop-filter]:bg-background/70"
      style={{ paddingBottom: 'env(safe-area-inset-bottom, 0px)' }}
      aria-label="Main navigation"
    >
      <div className="mx-auto flex max-w-4xl items-center justify-around">
        {tabs.map((tab) => {
          const isActive =
            pathname === tab.path ||
            (tab.key === 'profile' && pathname === '/settings') ||
            (tab.key === 'dashboard' && pathname === '/dashboard');
          const Icon = tab.icon;
          const isDisabled = !isVerified && tab.key !== 'profile';

          const sharedClassName = cn(
            'relative flex flex-1 flex-col items-center gap-0.5 py-2 text-xs font-medium transition-all duration-200',
            'min-h-[56px] justify-center',
            isActive
              ? 'text-primary'
              : 'text-muted-foreground hover:text-foreground',
            isDisabled && 'opacity-40 pointer-events-none',
          );

          const content = (
            <>
              {isActive && (
                <span className="absolute inset-x-4 top-0 h-[3px] rounded-full bg-primary animate-fade-in" />
              )}
              <div
                className={cn(
                  'flex size-9 items-center justify-center rounded-xl transition-all duration-200',
                  isActive && 'bg-primary/10 scale-105',
                )}
              >
                <Icon
                  className={cn(
                    'size-5 transition-all duration-200',
                    isActive && 'size-[22px]',
                  )}
                  strokeWidth={isActive ? 2.5 : 2}
                  aria-hidden="true"
                />
              </div>
              <span className={cn(
                'font-display text-[10px] tracking-wide transition-all duration-200',
                isActive && 'font-semibold',
              )}>
                {tab.label}
              </span>
            </>
          );

          if (isDisabled) {
            return (
              <span
                key={tab.key}
                className={sharedClassName}
                aria-label={tab.label}
                aria-disabled="true"
              >
                {content}
              </span>
            );
          }

          return (
            <Link
              key={tab.key}
              href={tab.path}
              className={sharedClassName}
              aria-current={isActive ? 'page' : undefined}
              aria-label={tab.label}
            >
              {content}
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
