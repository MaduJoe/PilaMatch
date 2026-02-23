import { create } from 'zustand';
import type { UserResponse } from '@/lib/api-types';

interface AuthState {
  user: UserResponse | null;
  profileId: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;

  setUser: (user: UserResponse, profileId: string | null) => void;
  setLoading: (loading: boolean) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  user: null,
  profileId: null,
  isLoading: true,
  isAuthenticated: false,

  setUser: (user, profileId) =>
    set({ user, profileId, isAuthenticated: true, isLoading: false }),

  setLoading: (isLoading) => set({ isLoading }),

  logout: () =>
    set({ user: null, profileId: null, isAuthenticated: false, isLoading: false }),
}));
