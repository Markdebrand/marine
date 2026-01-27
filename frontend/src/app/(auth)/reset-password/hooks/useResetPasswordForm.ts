"use client";
import { useState, useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { authService } from "@/services/authService";

export function useResetPasswordForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token");

  const [values, setValues] = useState({
    password: "",
    confirmPassword: "",
  });
  const [loading, setLoading] = useState(false);
  const [verifying, setVerifying] = useState(true);
  const [isTokenValid, setIsTokenValid] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (!token) {
      setError("Reset token is missing from the URL.");
      setVerifying(false);
      return;
    }

    const verifyToken = async () => {
      try {
        const res = await authService.verifyResetToken(token);
        if (res.valid) {
          setIsTokenValid(true);
        } else {
          setError(res.message || "Invalid or expired token.");
        }
      } catch (err: any) {
        setError(err.message || "Failed to verify reset token.");
      } finally {
        setVerifying(false);
      }
    };

    verifyToken();
  }, [token]);

  const onChange = (field: "password" | "confirmPassword") => (e: React.ChangeEvent<HTMLInputElement>) => {
    setValues((v) => ({ ...v, [field]: e.target.value }));
    setFieldErrors((prev) => ({ ...prev, [field]: "" }));
  };

  const onSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!token) return;

    setError(null);
    setFieldErrors({});

    const errs: Record<string, string> = {};
    if (!values.password || values.password.length < 8) {
      errs.password = "Password must be at least 8 characters long";
    }
    if (values.password !== values.confirmPassword) {
      errs.confirmPassword = "Passwords do not match";
    }

    if (Object.keys(errs).length > 0) {
      setFieldErrors(errs);
      return;
    }

    setLoading(true);
    try {
      const res = await authService.resetPassword({
        token,
        new_password: values.password,
      });
      if (res.ok) {
        setSuccess(true);
      } else {
        setError(res.message || "Failed to reset password. Please try again.");
      }
    } catch (err: any) {
      setError(err.message || "An error occurred while resetting your password.");
    } finally {
      setLoading(false);
    }
  };

  return {
    values,
    loading,
    verifying,
    isTokenValid,
    error,
    success,
    fieldErrors,
    onChange,
    onSubmit,
  };
}
