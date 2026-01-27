"use client";
import { useState } from "react";
import { authService } from "@/services/authService";

export function useForgotPasswordForm() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [fieldError, setFieldError] = useState<string | null>(null);

  const onChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setEmail(e.target.value);
    setFieldError(null);
  };

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setFieldError(null);
    setSuccess(null);

    if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim())) {
      setFieldError("Please enter a valid email address");
      return;
    }

    const cleanEmail = email.trim().toLowerCase();
    setLoading(true);
    try {
      const res = await authService.forgotPassword(cleanEmail);
      if (res.ok) {
        setSuccess("If that email exists in our system, we've sent a password reset link.");
      } else {
        setError(res.message || "Something went wrong. Please try again.");
      }
    } catch (err: any) {
      setError(err.message || "Failed to send reset link");
    } finally {
      setLoading(false);
    }
  };

  return { email, loading, error, success, fieldError, onChange, onSubmit };
}
