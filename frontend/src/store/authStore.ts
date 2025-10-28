
"use client";
import { create } from "zustand";
import { persist } from "zustand/middleware";

export type AuthUser = {
  id: number;
  email: string;
  role?: string | null;
  is_superadmin?: boolean | null;
};

type AuthState = {
  status: "idle" | "loading" | "authenticated" | "unauthenticated";
  user: AuthUser | null;
  accessToken: string | null;
  refreshToken: string | null;
  loginAt: number | null;
  setStatus: (s: AuthState["status"]) => void;
  setUser: (u: AuthUser | null) => void;
  setAccessToken: (t: string | null) => void;
  setRefreshToken: (t: string | null) => void;
  setLoginAt: (ts: number | null) => void;
  resetAuth: () => void;
};

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      status: "idle",
      user: null,
      accessToken: null,
      refreshToken: null,
      loginAt: null,
      setStatus: (s) => set({ status: s }),
      setUser: (u) => set({ user: u }),
      setAccessToken: (t) => set({ accessToken: t }),
      setRefreshToken: (t) => set({ refreshToken: t }),
      setLoginAt: (ts) => set({ loginAt: ts }),
      resetAuth: () => set({ status: "unauthenticated", user: null, accessToken: null, refreshToken: null, loginAt: null }),
    }),
    {
      name: "auth-storage",
      partialize: (state) => ({
        status: state.status,
        user: state.user,
        accessToken: state.accessToken,
        refreshToken: state.refreshToken,
        loginAt: state.loginAt,
      }),
    }
  )
);
