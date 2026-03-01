'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useAuthStore } from '@/stores/auth-store';
import { Search, ClipboardList, User, Megaphone, Users } from 'lucide-react';
import { cn } from '@/lib/utils';

const INSTRUCTOR_TABS = [
  { key: 'jobs', label: '일 찾기', icon: Search, path: '/steps/jobs' },
  { key: 'offers', label: '내 지원', icon: ClipboardList, path: '/steps/offers' },
  { key: 'profile', label: '프로필', icon: User, path: '/steps/profile' },
] as const;

const STUDIO_TABS = [
  { key: 'jobs', label: '공고 관리', icon: Megaphone, path: '/steps/jobs' },
  { key: 'offers', label: '지원자', icon: Users, path: '/steps/offers' },
  { key: 'profile', label: '프로필', icon: User, path: '/steps/profile' },
] as const;

export function BottomTabBar() {
  const pathname = usePathname();
  const user = useAuthStore((s) => s.user);

  if (!user) return null;

  const tabs = user.role === 'instructor' ? INSTRUCTOR_TABS : STUDIO_TABS;

  return (
    <nav
      className="fixed bottom-0 left-0 right-0 z-40 border-t bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/80"
      style={{ paddingBottom: 'env(safe-area-inset-bottom, 0px)' }}
      aria-label="메인 네비게이션"
    >
      <div className="mx-auto flex max-w-4xl items-center justify-around">
        {tabs.map((tab) => {
          const isActive =
            pathname === tab.path ||
            (tab.key === 'profile' && pathname === '/settings');
          const Icon = tab.icon;

          return (
            <Link
              key={tab.key}
              href={tab.path}
              className={cn(
                'flex flex-1 flex-col items-center gap-0.5 py-2 text-xs font-medium transition-colors',
                'min-h-[56px] justify-center',
                isActive
                  ? 'text-primary'
                  : 'text-muted-foreground hover:text-foreground',
              )}
              aria-current={isActive ? 'page' : undefined}
              aria-label={tab.label}
            >
              <Icon
                className={cn('size-5', isActive && 'size-[22px]')}
                aria-hidden="true"
              />
              <span>{tab.label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
