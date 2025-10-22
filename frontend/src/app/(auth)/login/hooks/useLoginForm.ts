"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import type { AuthCredentials } from "../types/auth";
import { login as loginRequest } from "../services/authClient";
import { useAuthStore } from "@/store/authStore";
import { authService } from "@/services/authService";

export function useLoginForm() {
  const [values, setValues] = useState<AuthCredentials>({
    email: "",
    password: "",
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<Partial<Record<keyof AuthCredentials, string>>>({});
  const router = useRouter();
  const { setStatus, setUser } = useAuthStore();

  const onChange =
    (field: keyof AuthCredentials) =>
    (e: React.ChangeEvent<HTMLInputElement>) =>
      setValues((v) => ({ ...v, [field]: e.target.value }));

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setFieldErrors({});
    // validate
    const errs: Partial<Record<keyof AuthCredentials, string>> = {};
    if (!values.email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(values.email)) {
      errs.email = "Please enter a valid email address";
    }
    if (!values.password || values.password.length < 8) {
      errs.password = "Password must be at least 8 characters";
    }
    if (Object.keys(errs).length > 0) {
      setFieldErrors(errs);
      setLoading(false);
      return;
    }
    setLoading(true);
    try {
      await loginRequest(values);
      // Cargamos el perfil para confirmar autenticación
      const me = await authService.me();
      setUser(me);
      setStatus("authenticated");
      router.replace("/map");
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Login failed";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return { values, loading, error, fieldErrors, onChange, onSubmit };
}
