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
    <header className="sticky top-0 z-30 border-b border-border/50 bg-background/90 backdrop-blur-xl supports-[backdrop-filter]:bg-background/70">
      <div className="mx-auto flex max-w-4xl items-center justify-between px-4 py-2.5">
        <Link href="/steps/jobs" className="group flex items-baseline gap-0.5">
          <span className="font-display text-xl font-bold tracking-tight text-primary transition-colors group-hover:text-primary/80">
            Pila
          </span>
          <span className="font-display text-xl font-bold tracking-tight text-foreground transition-colors group-hover:text-foreground/80">
            Match
          </span>
        </Link>
        <div className="flex items-center gap-1">
          <NotificationBell />
          <Button
            variant="ghost"
            size="icon"
            className="size-9 text-muted-foreground hover:text-foreground"
            asChild
          >
            <Link href="/settings" aria-label="Settings">
              <Settings className="size-4" aria-hidden="true" />
            </Link>
          </Button>
        </div>
      </div>
    </header>
  );
}
