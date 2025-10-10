"use client";
import Image from "next/image";
import Link from "next/link";
import { useLoginForm } from "../hooks/useLoginForm";

export default function LoginCard() {
  const { values, loading, error, onChange, onSubmit } = useLoginForm();

  return (
    <div className="w-full max-w-lg rounded-2xl glass-card p-6">
      <div className="mb-4 text-center">
        <div className="flex flex-col items-center gap-3">
          <Image src="/Icon.png" alt="HSO MARINE" width={56} height={56} className="h-14 w-14" />
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
        <input
          className="bg-white/20 backdrop-blur-sm border border-white/8 rounded-md px-4 py-3 placeholder:text-slate-400 text-slate-900 focus:outline-none focus:ring-2 focus:ring-slate-200"
          placeholder="Password"
          type="password"
          value={values.password}
          onChange={onChange("password")}
        />
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
