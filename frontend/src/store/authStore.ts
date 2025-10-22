"use client";
import { create, StateCreator } from "zustand";

interface AuthState {
  token: string | null;
  setToken: (t: string | null) => void;
}

const STORAGE_KEY = "auth_token";

const createAuthSlice: StateCreator<AuthState, [], [], AuthState> = (set) => ({
  token: typeof window !== "undefined" ? localStorage.getItem(STORAGE_KEY) : null,
  setToken: (t) => {
    if (typeof window !== "undefined") {
      if (t) localStorage.setItem(STORAGE_KEY, t);
      else localStorage.removeItem(STORAGE_KEY);
    }
    set({ token: t });
  },
});

export const useAuthStore = create<AuthState>()(createAuthSlice);
