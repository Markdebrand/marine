"use client";
import { useEffect, useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { usePathname, useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { Phone, Globe, User } from 'lucide-react';

const NAV_LINKS = [
  { href: "/", label: "Home" },
  { href: "/about", label: "About Us" },
  { href: "/services", label: "Services" },
  { href: "/contact", label: "Contact Us" },
] as const;

// IconPhone removed - using lucide-react Phone icon instead

// Removed IconGlobe function definition

// Replaced IconUser function with lucide-react User component

function IconMenu({ className = "w-7 h-7" }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
      strokeWidth={1.5}
      stroke="currentColor"
      className={className}
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M3.75 6.75h16.5M3.75 12h16.5M3.75 17.25h16.5"
      />
    </svg>
  );
}

function IconClose({ className = "w-7 h-7" }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      fill="none"
      viewBox="0 0 24 24"
      strokeWidth={1.5}
      stroke="currentColor"
      className={className}
    >
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        d="M6 18L18 6M6 6l12 12"
      />
    </svg>
  );
}

function Navbar() {
  const { status, user } = useAuth();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [mounted, setMounted] = useState(false);
  const pathname = usePathname();
  const router = useRouter();
  // Evitar mismatch SSR/CSR: mantener href estable en SSR y cambiar tras montar
  const ctaHref = mounted && status === "authenticated" ? "/map" : "/login";

  // Prefetch common routes to speed up header navigation
  useEffect(() => {
    try {
      NAV_LINKS.forEach((l) => router.prefetch(l.href));
    } catch {}
  }, [router]);

  // Marcar como montado para poder cambiar CTA sin causar hydration error
  useEffect(() => setMounted(true), []);

  return (
    <header className="w-full bg-transparent sticky top-0 z-50 pt-3">
      <nav
        className="mx-auto w-11/12 max-w-7xl glass-card px-4 sm:px-6 lg:px-8 py-3 sm:py-4 flex items-center justify-between"
        aria-label="Main navigation"
      >
        {/* Logo + Desktop Navigation grouped to keep links close to the brand */}
        <div className="flex items-center gap-4">
          <Link
            href="/"
            className="flex items-center gap-3 text-slate-900"
            aria-label="Go home"
          >
            {/* Show wordmark on sm+ screens: keep it inline and constrained to avoid large gaps */}
            <div className="hidden sm:flex flex-col leading-none">
              <Image
                src="/HSOMarineLogo.svg"
                alt="HSO MARINE"
                width={200}
                height={36}
                className="h-12 w-auto"
              />
            </div>
          </Link>

          <div className="hidden lg:flex items-center gap-2 text-[16px]">
            {NAV_LINKS.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                prefetch
                onMouseEnter={() => {
                  try {
                    router.prefetch(link.href);
                  } catch {}
                }}
                className={`transition-colors hover:text-red-600 ${
                  pathname === link.href ||
                  (link.href !== "/" && pathname.startsWith(link.href))
                    ? "underline underline-offset-8 decoration-2 decoration-red-600 text-red-600"
                    : "text-slate-800"
                }`}
              >
                {link.label}
              </Link>
            ))}
          </div>
        </div>

        {/* Right controls (pushed to the far right) */}
        <div className="hidden md:flex items-center gap-4 text-[16px] ml-auto">
          <a
            href="tel:+16625639786"
            className="hidden lg:flex items-center gap-2 text-slate-600 hover:text-slate-800"
          >
            <Phone className="h-4 w-4" />
            <span className="whitespace-nowrap">+1 (662) 563-9786</span>
          </a>
          <button
            aria-label="Language"
            className="hidden md:inline-flex items-center justify-center text-slate-600 hover:text-slate-800"
          >
            <Globe className="h-4 w-4" />
          </button>
          <Link
            href="/login"
            className="inline-flex items-center gap-3 hover:bg-white/5 rounded-md px-2 py-1"
          >
            <span className="inline-flex items-center justify-center rounded-md bg-white/5 text-slate-700 p-1.5">
              <User className="h-4 w-4 text-slate-700" />
            </span>
            <span className="text-slate-800 font-medium">Login</span>
          </Link>
          <Link
            href={ctaHref}
            className="inline-flex items-center rounded-xl bg-red-600 px-6 py-3 text-white text-base font-medium hover:bg-red-700 shadow ml-6"
          >
            Start Trade
          </Link>
        </div>

        {/* Mobile header: show logo + quick controls (phone, login) and menu toggle */}
        <div className="lg:hidden flex items-center w-full gap-3">
          <Link href="/" className="flex items-center gap-2" aria-label="Go home">
            <Image src="/HSOMarineLogo.svg" alt="HSO" width={32} height={32} className="h-10 w-auto" />
          </Link>

          <div className="ml-auto flex items-center gap-2">
            <a href="tel:+16625639786" className="hidden sm:inline-flex items-center gap-2 text-slate-600 hover:text-slate-800">
              <Phone className="h-4 w-4" />
            </a>

            <Link href="/login" className="inline-flex items-center gap-2 text-slate-800 hover:bg-white/5 rounded-md px-2 py-1">
              <span className="inline-flex items-center justify-center rounded-md bg-white/5 text-slate-700 p-1">
                <User className="h-4 w-4 text-slate-700" />
              </span>
            </Link>

            <button
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              className="p-2 text-slate-900"
              aria-label="Toggle menu"
              type="button"
            >
              {isMenuOpen ? <IconClose /> : <IconMenu />}
            </button>
          </div>
        </div>
      </nav>

      {/* Mobile Navigation */}
      {isMenuOpen && (
        <div className="lg:hidden mt-2">
          <div className="mx-auto w-11/12 max-w-7xl glass-card px-4 py-3 flex flex-col gap-4">
            
            {NAV_LINKS.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                prefetch
                onMouseEnter={() => {
                  try {
                    router.prefetch(link.href);
                  } catch {}
                }}
                className={`transition-colors hover:text-red-600 ${
                  pathname === link.href ||
                  (link.href !== "/" && pathname.startsWith(link.href))
                    ? "underline underline-offset-6 decoration-2 decoration-red-600 text-red-600"
                    : "text-slate-800"
                }`}
                onClick={() => setIsMenuOpen(false)}
              >
                {link.label}
              </Link>
            ))}
            <div className="pt-2 flex items-center gap-3">
              
              <Link
                href={ctaHref}
                className="inline-flex items-center rounded-xl bg-red-600 px-6 py-3 text-white text-base font-medium hover:bg-red-700 w-full justify-center shadow"
              >
                Start Trade
              </Link>
            </div>
          </div>
        </div>
      )}
    </header>
  );
}

export { Navbar };
export default Navbar;
