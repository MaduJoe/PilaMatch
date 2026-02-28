'use client';

import { useAuthStore } from '@/stores/auth-store';
import { useLogout } from '@/hooks/use-auth';
import { Button } from '@/components/ui/button';
import { LogOut } from 'lucide-react';
import { ThemeToggle } from '@/components/theme-toggle';
import { NotificationBell } from '@/components/notification/notification-bell';

export function Header() {
  const { user } = useAuthStore();
  const logout = useLogout();

  if (!user) return null;

  const isInstructor = user.role === 'instructor';
  const roleText = isInstructor ? '강사' : '스튜디오';
  const userName = isInstructor ? user.display_name : user.business_name;

  return (
    <header className="border-b bg-background">
      <div className="mx-auto flex max-w-4xl items-center justify-between px-4 py-3">
        <div>
          <h1 className="text-lg font-bold text-gray-900 sm:text-xl">
            PilaMatch - {roleText}
          </h1>
        </div>
        <div className="flex items-center gap-3">
          <div className="text-right">
            <p className="text-sm font-medium text-gray-700">{user.email}</p>
            <p className="text-xs text-gray-500">
              {userName || '프로필을 완성해주세요'}
            </p>
          </div>
          <NotificationBell />
          <ThemeToggle />
          <Button
            variant="ghost"
            size="sm"
            onClick={() => logout.mutate()}
            disabled={logout.isPending}
            aria-label="로그아웃"
          >
            <LogOut className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </header>
  );
}
