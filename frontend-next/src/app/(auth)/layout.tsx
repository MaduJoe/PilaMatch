'use client';

import { useEffect, useState } from 'react';

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  return (
    <div className="auth-gradient grain-overlay relative flex min-h-dvh flex-col items-center justify-center px-4 py-12 overflow-hidden">
      {/* Decorative floating shapes */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden="true">
        <div className="absolute -top-24 -right-24 size-96 rounded-full bg-primary/[0.04] blur-3xl" />
        <div className="absolute -bottom-32 -left-32 size-[28rem] rounded-full bg-success/[0.04] blur-3xl" />
        <div className="absolute top-1/3 right-1/4 size-64 rounded-full bg-urgent/[0.03] blur-3xl" />
      </div>

      <div
        className={`relative z-10 w-full max-w-[420px] transition-all duration-700 ease-out ${
          mounted ? 'translate-y-0 opacity-100' : 'translate-y-6 opacity-0'
        }`}
      >
        {/* Brand header */}
        <div className="mb-10 text-center">
          <div className="mb-4 inline-flex items-center justify-center">
            <div className="relative">
              <span className="font-display text-4xl font-extrabold tracking-tight text-primary">
                Pila
              </span>
              <span className="font-display text-4xl font-extrabold tracking-tight text-foreground">
                Match
              </span>
              <div className="absolute -bottom-1 left-0 h-[3px] w-full rounded-full bg-gradient-to-r from-primary via-primary/60 to-transparent" />
            </div>
          </div>
          <p className="mt-3 text-sm font-medium text-muted-foreground tracking-wide">
            Trust-based substitute matching
          </p>
        </div>

        {/* Form card */}
        <div className="rounded-2xl border border-border/60 bg-card/80 p-6 shadow-xl shadow-primary/[0.04] backdrop-blur-sm sm:p-8">
          {children}
        </div>

        {/* Footer */}
        <p className="mt-8 text-center text-xs text-muted-foreground/60">
          &copy; 2026 PilaMatch. All rights reserved.
        </p>
      </div>
    </div>
  );
}
