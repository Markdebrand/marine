"use client";
import { useAuthStore } from "@/store/authStore";

export function useAuth() {
  const { token, setToken } = useAuthStore();
  return { token, setToken };
}
