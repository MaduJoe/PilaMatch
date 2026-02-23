'use client';

import { useEffect } from 'react';
import { useAuthStore } from '@/stores/auth-store';
import type { MeResponse } from '@/lib/api-types';

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const { setUser, setLoading } = useAuthStore();

  useEffect(() => {
    async function loadUser() {
      try {
        // Use BFF route (/api/auth/me) instead of /api/v1/auth/me
        // The BFF route reads the httpOnly cookie and injects the Bearer token
        const res = await fetch('/api/auth/me');
        if (!res.ok) throw new Error('Not authenticated');
        const data: MeResponse = await res.json();
        setUser(data.user, data.profile_id ?? null);
      } catch {
        // Not authenticated - that's fine
      } finally {
        setLoading(false);
      }
    }
    loadUser();
  }, [setUser, setLoading]);

  return <>{children}</>;
}
