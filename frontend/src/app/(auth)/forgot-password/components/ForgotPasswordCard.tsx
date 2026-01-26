"use client";
import Image from "next/image";
import Link from "next/link";
import { useForgotPasswordForm } from "../hooks/useForgotPasswordForm";
import { ArrowLeft } from "lucide-react";

export default function ForgotPasswordCard() {
  const { email, loading, error, success, fieldError, onChange, onSubmit } = useForgotPasswordForm();

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
        <h1 className="text-slate-900 text-xl font-semibold mt-4">Forgot Password?</h1>
        <p className="text-slate-600 text-sm mt-2">
          Enter your email address and we'll send you a link to reset your password.
        </p>
      </div>

      {!success ? (
        <form noValidate className="grid gap-4" onSubmit={onSubmit}>
          <div>
            <label className="sr-only" htmlFor="email">Email</label>
            <input
              id="email"
              className="bg-white/20 backdrop-blur-sm border border-white/8 rounded-md px-4 py-3 placeholder:text-slate-400 text-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-200 w-full"
              placeholder="Email address"
              type="email"
              required
              value={email}
              onChange={onChange}
            />
            {fieldError && (
              <p className="text-red-500 text-sm mt-1">{fieldError}</p>
            )}
          </div>

          {error && (
            <p role="alert" className="text-red-500 text-sm mt-1">
              {error}
            </p>
          )}

          <button
            className="mt-2 w-full md:w-2/3 mx-auto block rounded-md bg-red-600 px-6 py-2.5 text-white text-sm font-medium hover:bg-red-700 disabled:opacity-50 transition-colors"
            disabled={loading}
          >
            {loading ? "Sending..." : "SEND RESET LINK"}
          </button>

          <div className="text-center mt-4">
            <Link
              href="/login"
              className="inline-flex items-center gap-2 text-sm text-slate-900 hover:underline"
            >
              <ArrowLeft className="h-4 w-4" />
              Back to login
            </Link>
          </div>
        </form>
      ) : (
        <div className="text-center py-4">
          <div className="mb-4 text-green-600 bg-green-50 p-4 rounded-lg border border-green-100">
            <p className="text-sm font-medium">{success}</p>
          </div>
          <Link
            href="/login"
            className="mt-6 inline-block rounded-md bg-slate-900 px-6 py-2.5 text-white text-sm font-medium hover:bg-slate-800 transition-colors"
          >
            Return to Login
          </Link>
        </div>
      )}
    </div>
  );
}
