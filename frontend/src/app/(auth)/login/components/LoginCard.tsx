"use client";
import { useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { Eye, EyeOff } from 'lucide-react';
import { useLoginForm } from "../hooks/useLoginForm";

export default function LoginCard() {
  const { values, loading, error, fieldErrors, onChange, onSubmit } = useLoginForm();
  const [showPassword, setShowPassword] = useState<boolean>(false);

  return (
    <div className="w-full max-w-lg rounded-2xl glass-card p-6">
      <div className="mb-4 text-center">
        <div className="flex flex-col items-center gap-3">
          <Image
            src="/HSOMarineLogo.svg"
            alt="HSO MARINE"
            width={140}
            height={36}
            className="h-14 w-auto"
          />
          <span className="sr-only">HSO MARINE</span>
        </div>
        <p className="text-slate-900 text-sm mt-1">Welcome back</p>
      </div>
  <form noValidate className="grid gap-4" onSubmit={onSubmit} onInvalid={(e) => e.preventDefault()}>
        <div>
          <label className="sr-only" htmlFor="email">Email</label>
          <input
            id="email"
            aria-invalid={!!fieldErrors?.email}
            aria-describedby={fieldErrors?.email ? 'email-error' : undefined}
            className="bg-white/20 backdrop-blur-sm border border-white/8 rounded-md px-4 py-3 placeholder:text-slate-400 text-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-200 w-full"
            placeholder="Email"
            type="email"
            value={values.email}
            onChange={onChange("email")}
          />
          {fieldErrors?.email && (
            <p id="email-error" className="text-red-500 text-sm mt-1">{fieldErrors.email}</p>
          )}
        </div>

        <div className="relative">
          <label className="sr-only" htmlFor="password">Password</label>
          <input
            id="password"
            aria-invalid={!!fieldErrors?.password}
            aria-describedby={fieldErrors?.password ? 'password-error' : undefined}
            className="bg-white/20 backdrop-blur-sm border border-white/8 rounded-md px-4 py-3 placeholder:text-slate-400 text-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-200 w-full pr-10"
            placeholder="Password"
            type={showPassword ? 'text' : 'password'}
            value={values.password}
            onChange={onChange("password")}
          />
          <button
            type="button"
            onClick={() => setShowPassword((s) => !s)}
            className="absolute right-2 top-1/2 -translate-y-1/2 text-slate-600 p-1"
            aria-label={showPassword ? 'Hide password' : 'Show password'}
            title={showPassword ? 'Hide password' : 'Show password'}
          >
            {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
          </button>
          {fieldErrors?.password && (
            <p id="password-error" className="text-red-500 text-sm mt-1">{fieldErrors.password}</p>
          )}
        </div>

        {error && (
          <p role="alert" aria-live="assertive" className="text-red-500 text-sm mt-1">
            {error}
          </p>
        )}
        <div className="flex items-center justify-between text-sm text-slate-900">
          <label className="flex items-center gap-2">
            <input type="checkbox" /> Remember me
          </label>
          <a href="#" className="hover:underline">
            Forgot?
          </a>
        </div>
        <button
          className="mt-3 w-2/3 md:w-1/2 mx-auto block rounded-md bg-red-600 px-6 py-2.5 text-white text-sm font-medium hover:bg-red-700 disabled:opacity-50"
          disabled={loading}
        >
          {loading ? "Signing in…" : "LOG IN"}
        </button>
      </form>
      <div className="text-sm text-slate-900 mt-4 text-center">
        Don’t have an account?{" "}
        <Link href="#" className="underline">
          Sign up
        </Link>
      </div>
    </div>
  );
}
