"use client";
import { useState } from "react";
import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";

const NAV_LINKS = [
  { href: "/", label: "Home" },
  { href: "/about", label: "About Us" },
  { href: "/services", label: "Services" },
  { href: "/contact", label: "Contact Us" },
] as const;

function IconPhone({ className = "h-4 w-4" }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="currentColor"
      className={className}
    >
      <path d="M2 3.5A1.5 1.5 0 0 1 3.5 2h2A1.5 1.5 0 0 1 7 3.5V6a1.5 1.5 0 0 1-1 1.414c.27.74.63 1.459 1.08 2.152a17 17 0 0 0 3.354 3.354c.693.45 1.412.81 2.152 1.08A1.5 1.5 0 0 1 14 14h2.5A1.5 1.5 0 0 1 18 15.5v2A1.5 1.5 0 0 1 16.5 19h-1A13.5 13.5 0 0 1 2 5.5v-2Z" />
    </svg>
  );
}

function IconGlobe({ className = "h-4 w-4" }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="currentColor"
      className={className}
    >
      <path d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20Zm0 2c1.53 0 2.93.43 4.13 1.17-.4.3-.82.55-1.26.75-.88.39-1.87.58-2.87.58s-1.99-.19-2.87-.58A7.94 7.94 0 0 1 7.87 5.17 7.98 7.98 0 0 1 12 4Zm-6 8c0-.69.1-1.36.29-2 .79.47 1.64.83 2.53 1.06 1.06.28 2.16.42 3.18.42s2.12-.14 3.18-.42c.89-.23 1.74-.59 2.53-1.06.19.64.29 1.31.29 2s-.1 1.36-.29 2a9.94 9.94 0 0 1-2.53-1.06A13.5 13.5 0 0 1 12 12c-1.02 0-2.12.14-3.18.42A9.94 9.94 0 0 1 6.29 14 7.98 7.98 0 0 1 6 12Zm6 8a7.98 7.98 0 0 1-4.13-1.17c.4-.3.82-.55 1.26-.75.88-.39 1.87-.58 2.87-.58s1.99.19 2.87.58c.44.2.86.45 1.26.75A7.98 7.98 0 0 1 12 20Z" />
    </svg>
  );
}

function IconUser({ className = "h-4 w-4" }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="currentColor"
      className={className}
    >
      <path d="M12 2a5 5 0 1 1 0 10 5 5 0 0 1 0-10Zm0 12c4.42 0 8 2.24 8 5v1H4v-1c0-2.76 3.58-5 8-5Z" />
    </svg>
  );
}

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
  const { token } = useAuth();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const pathname = usePathname();
  const ctaHref = token ? "/map" : "/login";

  return (
    <header className="w-full bg-white">
      <nav
        className="mx-auto w-11/12 max-w-7xl p-5 flex items-center justify-between"
        aria-label="Main navigation"
      >
        {/* Logo + Desktop Navigation grouped to keep links close to the brand */}
        <div className="flex items-center gap-4">
          <Link
            href="/"
            className="flex items-center gap-2 font-bold text-[24px] text-slate-900"
            aria-label="Go home"
          >
            <Image
              src="/icon.png"
              alt="HSO MARINE"
              width={28}
              height={28}
              className="h-7 w-7"
            />
            <span className="tracking-wide">HSO MARINE</span>
          </Link>

          <div className="hidden lg:flex items-center gap-4 text-[16px]">
            {NAV_LINKS.map((link) => (
              <Link
                key={link.href}
                href={link.href}
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
            <IconPhone />
            <span className="whitespace-nowrap">+1 (662) 563-9786</span>
          </a>
          <button
            aria-label="Language"
            className="hidden md:inline-flex items-center justify-center text-slate-600 hover:text-slate-800"
          >
            <IconGlobe />
          </button>
          <Link
            href="/login"
            className="inline-flex items-center gap-2 text-slate-900 font-semibold tracking-wide"
          >
            <IconUser />
            <span>LOG IN</span>
          </Link>
          <Link
            href={ctaHref}
            className="inline-flex items-center rounded-xl bg-red-600 px-6 py-3 text-white text-base font-medium hover:bg-red-700 shadow ml-6"
          >
            Start Trade
          </Link>
        </div>

        {/* Mobile Menu Button */}
        <div className="lg:hidden">
          <button
            onClick={() => setIsMenuOpen(!isMenuOpen)}
            className="text-slate-900"
            aria-label="Toggle menu"
            type="button"
          >
            {isMenuOpen ? <IconClose /> : <IconMenu />}
          </button>
        </div>
      </nav>

      {/* Mobile Navigation */}
      {isMenuOpen && (
        <div className="lg:hidden border-t border-zinc-200">
          <div className="mx-auto w-11/12 max-w-7xl px-0 py-3 flex flex-col gap-4">
            {NAV_LINKS.map((link) => (
              <Link
                key={link.href}
                href={link.href}
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
                href="/login"
                className="inline-flex items-center gap-2 text-slate-900"
              >
                <IconUser />
                <span>LOG IN</span>
              </Link>
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
