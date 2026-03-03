'use client';

import Link from 'next/link';
import { useAuthStore } from '@/stores/auth-store';
import { Button } from '@/components/ui/button';
import { Settings } from 'lucide-react';
import { NotificationBell } from '@/components/notification/notification-bell';

export function Header() {
  const { user } = useAuthStore();

  if (!user) return null;

  return (
    <header className="sticky top-0 z-30 border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/80">
      <div className="mx-auto flex max-w-4xl items-center justify-between px-4 py-2.5">
        <Link href="/steps/jobs" className="text-lg font-bold text-primary">
          PilaMatch
        </Link>
        <div className="flex items-center gap-1.5">
          <NotificationBell />
          <Button
            variant="ghost"
            size="icon"
            className="size-9"
            asChild
          >
            <Link href="/settings" aria-label="설정">
              <Settings className="size-4" aria-hidden="true" />
            </Link>
          </Button>
        </div>
      </div>
    </header>
  );
}
