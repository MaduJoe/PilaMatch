'use client';

import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuthStore } from '@/stores/auth-store';
import { APIError } from '@/lib/api-client';
import type { SignupRequest, MeResponse } from '@/lib/api-types';
import { toast } from 'sonner';

async function fetchBFF<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(path, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const detail = body.detail;
    const code = typeof detail === 'object' ? detail.code : 'UNKNOWN';
    const message = typeof detail === 'object'
      ? detail.message
      : typeof detail === 'string'
        ? detail
        : `HTTP ${res.status}`;
    throw new APIError(res.status, code, message);
  }

  return res.json();
}

export function useCurrentUser() {
  const { setUser, setLoading } = useAuthStore();

  return useQuery<MeResponse>({
    queryKey: ['auth', 'me'],
    queryFn: async () => {
      const data = await fetchBFF<MeResponse>('/api/auth/me');
      setUser(data.user, data.profile_id ?? null);
      return data;
    },
    retry: false,
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useLogin() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const queryClient = useQueryClient();
  const { setUser } = useAuthStore();

  return useMutation({
    mutationFn: async (data: { email: string; password: string }) => {
      await fetchBFF('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify(data),
      });

      // Fetch user data after login
      const me = await fetchBFF<MeResponse>('/api/auth/me');
      return me;
    },
    onSuccess: (data) => {
      setUser(data.user, data.profile_id ?? null);
      queryClient.setQueryData(['auth', 'me'], data);
      toast.success('로그인 성공!');
      const callbackUrl = searchParams.get('callbackUrl');
      router.push(callbackUrl || '/steps/profile');
    },
    onError: (error: Error) => {
      if (error instanceof APIError) {
        toast.error(error.message);
      } else {
        toast.error('로그인에 실패했습니다');
      }
    },
  });
}

export function useSignup() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { setUser } = useAuthStore();

  return useMutation({
    mutationFn: async (data: SignupRequest) => {
      await fetchBFF('/api/auth/signup', {
        method: 'POST',
        body: JSON.stringify(data),
      });

      // Fetch user data after signup
      const me = await fetchBFF<MeResponse>('/api/auth/me');
      return me;
    },
    onSuccess: (data) => {
      setUser(data.user, data.profile_id ?? null);
      queryClient.setQueryData(['auth', 'me'], data);
      toast.success('회원가입 성공!');
      router.push('/steps/profile');
    },
    onError: (error: Error) => {
      if (error instanceof APIError) {
        toast.error(error.message);
      } else {
        toast.error('회원가입에 실패했습니다');
      }
    },
  });
}

export function useLogout() {
  const router = useRouter();
  const queryClient = useQueryClient();
  const { logout } = useAuthStore();

  return useMutation({
    mutationFn: async () => {
      await fetchBFF('/api/auth/logout', { method: 'POST' });
    },
    onSuccess: () => {
      logout();
      queryClient.clear();
      router.push('/login');
    },
  });
}
