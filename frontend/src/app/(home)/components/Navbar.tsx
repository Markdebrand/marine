"use client";
import { useLayoutEffect, useState, useRef, useMemo } from "react";
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
  const { status } = useAuth();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const pathname = usePathname();
  const router = useRouter();
  const linksContainerRef = useRef<HTMLDivElement | null>(null);
  const [indicator, setIndicator] = useState({ left: 0, width: 0, opacity: 0 });
  // CTA dependiendo del estado de auth
  const ctaHref = useMemo(() => (status === "authenticated" ? "/map" : "/login"), [status]);

  // Prefetch common routes to speed up header navigation
  // Avoid prefetching everything on mount (can load extra JS). Let Link prefetch
  // handle common cases and optionally prefetch on hover.

  useLayoutEffect(() => {
    // Use a rAF-scheduled update and ResizeObserver to avoid layout thrashing
    let rafId: number | null = null;

    const doUpdate = () => {
      const container = linksContainerRef.current;
      if (!container) {
        setIndicator((s) => ({ ...s, opacity: 0 }));
        return;
      }

      // Find active link by matching href; choose longest matching prefix
      let activeHref: string | null = null;
      for (const l of NAV_LINKS) {
        if (l.href === "/" && pathname === "/") {
          activeHref = l.href;
        } else if (l.href !== "/" && pathname?.startsWith(l.href)) {
          activeHref = l.href;
          break;
        }
      }
      // fallback to exact match
      if (!activeHref) {
        for (const l of NAV_LINKS) if (l.href === pathname) activeHref = l.href;
      }
      if (!activeHref) {
        setIndicator((s) => ({ ...s, opacity: 0 }));
        return;
      }

      const anchor = container.querySelector<HTMLAnchorElement>(`a[href="${activeHref}"]`);
      if (!anchor) {
        setIndicator((s) => ({ ...s, opacity: 0 }));
        return;
      }
      const linkRect = anchor.getBoundingClientRect();
      const contRect = container.getBoundingClientRect();
      const left = Math.round(linkRect.left - contRect.left);
      const width = Math.round(linkRect.width);
      setIndicator({ left, width, opacity: 1 });
    };

    const scheduleUpdate = () => {
      if (rafId) cancelAnimationFrame(rafId);
      rafId = requestAnimationFrame(doUpdate) as unknown as number;
    };

    // initial run
    scheduleUpdate();

    // Use ResizeObserver on the links container so we only react to relevant changes
    let ro: ResizeObserver | null = null;
    const observed = linksContainerRef.current;
    try {
      if (typeof ResizeObserver !== "undefined" && observed) {
        ro = new ResizeObserver(scheduleUpdate);
        ro.observe(observed);
      } else {
        // fallback to window resize
        window.addEventListener("resize", scheduleUpdate);
      }
    } catch {
      window.addEventListener("resize", scheduleUpdate);
    }

    // also update after a short timeout to allow layout shifts
    const t = window.setTimeout(scheduleUpdate, 120);

    return () => {
      if (rafId) cancelAnimationFrame(rafId);
  if (ro && observed) ro.unobserve(observed);
      window.removeEventListener("resize", scheduleUpdate);
      clearTimeout(t);
    };
  }, [pathname]);

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
            {/* Compact logo for small screens, wordmark for lg+ */}
            <Image
              src="/HSOMarineLogo.svg"
              alt="HSO"
              width={32}
              height={32}
              className="h-10 w-auto block lg:hidden"
            />
            <div className="hidden lg:flex flex-col leading-none">
              <Image
                src="/HSOMarineLogo.svg"
                alt="HSO MARINE"
                width={200}
                height={36}
                className="h-12 w-auto"
              />
            </div>
          </Link>

          <div
            ref={linksContainerRef}
            className="hidden lg:flex items-center gap-8 text-[16px] relative pb-1"
          >
            {/* sliding indicator */}
            <div
              aria-hidden
              className="absolute left-0 h-0.5 bg-red-600 rounded transition-all duration-300 bottom-0.5"
              style={{ left: indicator.left, width: indicator.width, opacity: indicator.opacity }}
            />
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
                className={`transition-colors hover:text-red-600 leading-none py-1 ${
                  pathname === link.href ||
                  (link.href !== "/" && pathname.startsWith(link.href))
                    ? "text-red-600"
                    : "text-slate-800"
                }`}
              >
                {link.label}
              </Link>
            ))}
          </div>
        </div>

        {/* Right controls (pushed to the far right) */}
          <div className="hidden lg:flex items-center gap-4 text-[16px] ml-auto">
          <a
              href="tel:+16625639786"
              className="hidden lg:flex items-center gap-2 text-slate-600 hover:text-slate-800"
          >
            <Phone className="h-4 w-4" />
            <span className="whitespace-nowrap">+1 (662) 563-9786</span>
          </a>
          <button
            aria-label="Language"
            className="hidden lg:inline-flex items-center justify-center text-slate-600 hover:text-slate-800"
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
            Start Marine
          </Link>
        </div>

        {/* Mobile header: show logo + quick controls (phone, login) and menu toggle */}
        <div className="lg:hidden flex items-center gap-3">
          {/* Mobile header controls (logo moved to left link to avoid duplication) */}

          <div className="ml-auto flex items-center gap-2">
              <a href="tel:+16625639786" className="inline-flex items-center gap-2 text-slate-600 hover:text-slate-800">
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
                    ? "text-red-600"
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
                Start Marine
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
