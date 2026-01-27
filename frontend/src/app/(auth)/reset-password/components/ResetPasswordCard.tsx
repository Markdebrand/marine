"use client";
import { useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { useResetPasswordForm } from "../hooks/useResetPasswordForm";
import { Eye, EyeOff, CheckCircle2, AlertCircle } from "lucide-react";

export default function ResetPasswordCard() {
  const {
    values,
    loading,
    verifying,
    isTokenValid,
    error,
    success,
    fieldErrors,
    onChange,
    onSubmit,
  } = useResetPasswordForm();

  const [showPassword, setShowPassword] = useState(false);

  if (verifying) {
    return (
      <div className="w-full max-w-lg rounded-2xl glass-card p-8 flex flex-col items-center justify-center min-h-[300px]">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-600 mb-4"></div>
        <p className="text-slate-600">Verifying reset link...</p>
      </div>
    );
  }

  if (!isTokenValid && !success) {
    return (
      <div className="w-full max-w-lg rounded-2xl glass-card p-8 text-center">
        <div className="flex justify-center mb-4">
          <AlertCircle className="h-16 w-16 text-red-500" />
        </div>
        <h1 className="text-slate-900 text-xl font-semibold mb-2">Invalid Reset Link</h1>
        <p className="text-slate-600 mb-6">
          {error || "This password reset link is invalid or has expired."}
        </p>
        <Link
          href="/forgot-password"
          className="inline-block rounded-md bg-red-600 px-6 py-2.5 text-white text-sm font-medium hover:bg-red-700 transition-colors"
        >
          Request new link
        </Link>
      </div>
    );
  }

  return (
    <div className="w-full max-w-lg rounded-2xl glass-card p-6">
      <div className="mb-6 text-center">
        <div className="flex flex-col items-center gap-3">
          <Image
            src="/HSOMarineLogo.svg"
            alt="HSO MARINE"
            width={140}
            height={36}
            className="h-14 w-auto"
          />
        </div>
        <h1 className="text-slate-900 text-xl font-semibold mt-4">Reset Your Password</h1>
        <p className="text-slate-600 text-sm mt-2">
          Strong passwords help keep your information safe.
        </p>
      </div>

      {!success ? (
        <form noValidate className="grid gap-4" onSubmit={onSubmit}>
          <div className="relative">
            <label className="sr-only" htmlFor="password">New Password</label>
            <input
              id="password"
              className="bg-white/20 backdrop-blur-sm border border-white/8 rounded-md px-4 py-3 placeholder:text-slate-400 text-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-200 w-full pr-10"
              placeholder="New password"
              type={showPassword ? "text" : "password"}
              required
              value={values.password}
              onChange={onChange("password")}
            />
            <button
              type="button"
              onClick={() => setShowPassword((s) => !s)}
              className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-600 p-1"
            >
              {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
            {fieldErrors.password && (
              <p className="text-red-500 text-sm mt-1">{fieldErrors.password}</p>
            )}
          </div>

          <div>
            <label className="sr-only" htmlFor="confirmPassword">Confirm Password</label>
            <input
              id="confirmPassword"
              className="bg-white/20 backdrop-blur-sm border border-white/8 rounded-md px-4 py-3 placeholder:text-slate-400 text-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-200 w-full"
              placeholder="Confirm new password"
              type={showPassword ? "text" : "password"}
              required
              value={values.confirmPassword}
              onChange={onChange("confirmPassword")}
            />
            {fieldErrors.confirmPassword && (
              <p className="text-red-500 text-sm mt-1">{fieldErrors.confirmPassword}</p>
            )}
          </div>

          {error && (
            <div className="p-3 rounded-md bg-red-50 border border-red-100 flex items-start gap-2">
              <AlertCircle className="h-5 w-5 text-red-500 shrink-0 mt-0.5" />
              <p className="text-red-700 text-sm">{error}</p>
            </div>
          )}

          <button
            className="mt-2 w-full md:w-2/3 mx-auto block rounded-md bg-red-600 px-6 py-2.5 text-white text-sm font-medium hover:bg-red-700 disabled:opacity-50 transition-colors shadow-lg"
            disabled={loading}
          >
            {loading ? "Updating..." : "UPDATE PASSWORD"}
          </button>
        </form>
      ) : (
        <div className="text-center py-6">
          <div className="flex justify-center mb-4">
            <CheckCircle2 className="h-16 w-16 text-green-500" />
          </div>
          <h2 className="text-slate-900 text-xl font-semibold mb-2">Password Updated!</h2>
          <p className="text-slate-600 mb-8">
            Your password has been changed successfully. You can now use your new password to sign in.
          </p>
          <Link
            href="/login"
            className="w-full md:w-2/3 mx-auto flex items-center justify-center rounded-md bg-slate-900 px-6 py-2.5 text-white text-sm font-medium hover:bg-slate-800 transition-colors"
          >
            Back to Login
          </Link>
        </div>
      )}
    </div>
  );
}
