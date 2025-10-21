"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import type { AuthCredentials } from "../types/auth";
import { login as loginRequest } from "../services/authClient";

export function useLoginForm() {
  const [values, setValues] = useState<AuthCredentials>({ email: "", password: "" });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fieldErrors, setFieldErrors] = useState<{ email?: string; password?: string }>({});
  const router = useRouter();
  const { setToken } = useAuth();

  const onChange = (field: keyof AuthCredentials) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setValues((v) => ({ ...v, [field]: e.target.value }));

  const validate = (vals: AuthCredentials) => {
    const errs: { email?: string; password?: string } = {};
    // Email required + basic format
    if (!vals.email || !vals.email.trim()) {
      errs.email = 'El correo es obligatorio';
    } else {
      // basic email regex
      const emailRe = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRe.test(vals.email)) errs.email = 'Correo inválido';
    }
    // Password required + min length
    if (!vals.password) {
      errs.password = 'La contraseña es obligatoria';
    } else if (vals.password.length < 8) {
      errs.password = 'La contraseña debe tener al menos 8 caracteres';
    }
    setFieldErrors(errs);
    return Object.keys(errs).length === 0;
  };

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    // validate before sending
    const ok = validate(values);
    if (!ok) return;
    setLoading(true);
    try {
      const { token } = await loginRequest(values);
      setToken(token);
      router.replace("/map");
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Login failed";
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return { values, loading, error, fieldErrors, onChange, onSubmit, validate };
}
