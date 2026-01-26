"use client";
import Link from "next/link";
import ForgotPasswordCard from "./components/ForgotPasswordCard";

export default function ForgotPasswordPage() {
  return (
    <section className="relative min-h-screen grid md:grid-cols-2">
      {/* Fondo */}
      <div className="absolute inset-0 z-0">
        <div
          className="h-full w-full bg-cover bg-center"
          style={{
            backgroundImage: "url('/images/loginvessel.webp')",
          }}
        />
        <div className="absolute inset-0 bg-black/30" />
      </div>

      {/* Botón volver */}
      <Link
        href="/"
        aria-label="Volver al inicio"
        className="absolute left-4 top-4 z-20 inline-flex items-center justify-center h-10 w-10 rounded-md bg-white/80 hover:bg-white/90 shadow transition-colors"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          className="h-5 w-5 text-slate-900"
          viewBox="0 0 20 20"
          fill="currentColor"
          aria-hidden="true"
        >
          <path
            fillRule="evenodd"
            d="M12.293 16.293a1 1 0 010 1.414l-6-6a1 1 0 010-1.414l6-6a1 1 0 111.414 1.414L8.414 10l5.293 5.293a1 1 0 010 1.414z"
            clipRule="evenodd"
          />
        </svg>
      </Link>

      {/* Card */}
      <div className="flex items-center justify-center p-8 relative z-10 md:col-start-2">
        <ForgotPasswordCard />
      </div>
    </section>
  );
}
