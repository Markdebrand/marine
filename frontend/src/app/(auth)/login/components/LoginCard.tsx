"use client";
import Image from "next/image";
import Link from "next/link";
import { useState } from 'react';
import { useLoginForm } from "../hooks/useLoginForm";

export default function LoginCard() {
  const { values, loading, error, fieldErrors, onChange, onSubmit } = useLoginForm();
  const [showPassword, setShowPassword] = useState(false);

  return (
    <div className="w-full max-w-lg rounded-2xl glass-card p-6">
      <div className="mb-4 text-center">
        <div className="flex flex-col items-center gap-3">
          <Image src="/HSO Marine Isotype.svg" alt="HSO MARINE" width={56} height={56} className="h-14 w-14" />
          <span className="text-2xl font-semibold text-slate-900">HSO MARINE</span>
        </div>
        <p className="text-slate-900 text-sm mt-1">Welcome back</p>
      </div>
      <form className="grid gap-4" onSubmit={onSubmit}>
        <input
          className="bg-white/20 backdrop-blur-sm border border-white/8 rounded-md px-4 py-3 placeholder:text-slate-400 text-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-200"
          placeholder="Email"
          type="email"
          value={values.email}
          onChange={onChange("email")}
        />
        {fieldErrors?.email && <p className="text-red-500 text-sm">{fieldErrors.email}</p>}
        <div className="relative">
          <input
            className="bg-white/20 backdrop-blur-sm border border-white/8 rounded-md px-4 py-3 placeholder:text-slate-400 text-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-200 w-full pr-10"
            placeholder="Password"
            type={showPassword ? 'text' : 'password'}
            value={values.password}
            onChange={onChange("password")}
            aria-invalid={!!fieldErrors?.password}
          />
          <button
            type="button"
            aria-label={showPassword ? 'Hide password' : 'Show password'}
            onClick={() => setShowPassword((s) => !s)}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-700 p-1"
          >
            {showPassword ? (
              // eye-off
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" d="M3 3l18 18M9.88 9.88A3 3 0 0012 15a3 3 0 003-3c0-.34-.05-.67-.15-.98" />
                <path strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" d="M10.44 5.24A16.94 16.94 0 002.9 12c1.73 3.12 4.68 5.5 8.6 6.5" />
              </svg>
            ) : (
              // eye
              <svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" d="M2.98 12.44C4.7 7.86 8.8 5 12 5c3.2 0 7.3 2.86 9.02 7.44A17 17 0 0112 19a17 17 0 01-9.02-6.56z" />
                <path strokeWidth={1.5} strokeLinecap="round" strokeLinejoin="round" d="M12 15a3 3 0 100-6 3 3 0 000 6z" />
              </svg>
            )}
          </button>
        </div>
        {fieldErrors?.password && <p className="text-red-500 text-sm">{fieldErrors.password}</p>}
        {error && <p className="text-red-500 text-sm text-center">{error}</p>}
        <div className="flex items-center justify-between text-sm text-slate-900">
          <label className="flex items-center gap-2"><input type="checkbox" /> Remember me</label>
          <a href="#" className="hover:underline">Forgot?</a>
        </div>
        <button className="mt-3 w-2/3 md:w-1/2 mx-auto block rounded-md bg-red-600 px-6 py-2.5 text-white text-sm font-medium hover:bg-red-700" disabled={loading}>
          {loading ? "Signing in…" : "LOG IN"}
        </button>
      </form>
      <div className="text-sm text-slate-900 mt-4 text-center">
        Don’t have an account? <Link href="#" className="underline">Sign up</Link>
      </div>
    </div>
  );
}
