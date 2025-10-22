"use client";
import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { createPortal } from "react-dom";
import { useAuth } from "@/hooks/useAuth";

export default function AppHeader() {
  const pathname = usePathname();
  const { setToken } = useAuth();
  const [menuOpen, setMenuOpen] = useState(false);
  const btnRef = useRef<HTMLButtonElement | null>(null);
  const [menuPos, setMenuPos] = useState<{ top: number; left: number } | null>(null);
  const isMap = pathname === "/map" || pathname?.startsWith("/map/");
  const link = (href: string, label: string) => {
    const active = pathname === href;
    return (
      <Link
        href={href}
        className={`px-3 py-2 rounded-md text-sm ${active ? "text-red-600" : "text-slate-700 hover:text-slate-900"}`}
      >
        {label}
      </Link>
    );
  };

  const containerClass = isMap
    ? 'fixed inset-x-6 top-4 z-[100] pointer-events-auto'
    : 'sticky top-4 z-50';

  useEffect(() => {
    function onDocClick(e: MouseEvent) {
      if (!menuOpen) return;
      // if click outside button area, close
      const btn = btnRef.current;
      if (!btn) return;
      if (!(e.target instanceof Node)) return;
      if (!btn.contains(e.target)) {
        setMenuOpen(false);
        setMenuPos(null);
      }
    }
    document.addEventListener('click', onDocClick);
    return () => document.removeEventListener('click', onDocClick);
  }, [menuOpen]);

  return (
    <div className={containerClass}>
      <div className="mx-auto max-w-7xl px-6">
        <div className="glass-card flex items-center justify-between gap-4 p-3 border border-white/30 shadow-[0_10px_30px_rgba(2,6,23,0.06)] backdrop-blur-md">
          <div className="flex items-center gap-3">
            <Image src="/Icon.png" alt="MarinaLive" width={28} height={28} className="h-7 w-7" />
            <span className="font-semibold text-slate-900">HSO Marine</span>
          </div>
          <div className="flex items-center gap-2 relative">
            <nav className="flex items-center gap-2">
              {link("/dashboard", "Dashboard")}
              {link("/map", "Live Map")}
              {link("/watchlist", "Watchlist")}
            </nav>
            {/* Profile menu */}
            <div className="ml-2">
              <button
                ref={btnRef}
                type="button"
                className="h-9 w-9 rounded-full bg-red-600 text-white flex items-center justify-center shadow hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-red-500"
                aria-haspopup="menu"
                aria-expanded={menuOpen}
                onClick={() => {
                  if (!menuOpen && btnRef.current) {
                    const rect = btnRef.current.getBoundingClientRect();
                    // position menu below the button, align right edge
                    const top = rect.bottom + 8 + window.scrollY;
                    const left = Math.max(8, rect.right - 224 + window.scrollX);
                    setMenuPos({ top, left });
                  }
                  setMenuOpen((v) => !v);
                }}
              >
                <span className="sr-only">Open profile menu</span>
                A
              </button>
            </div>
          </div>
        </div>
      </div>
      {menuOpen && menuPos && createPortal(
        <div style={{ position: 'absolute', top: menuPos.top, left: menuPos.left, zIndex: 2000 }}>
          <div className="w-56 glass-dropdown rounded-md border border-white/30 shadow-[0_10px_30px_rgba(2,6,23,0.06)] py-2">
            <div className="px-3 py-2 text-sm text-slate-800 font-medium">AdminW</div>
            <div className="h-px bg-white/30 my-1" />
            <Link href="/profile" className="block px-3 py-2 text-sm text-slate-700 hover:bg-white/50">My Profile</Link>
            <Link href="/admin/sessions" className="block px-3 py-2 text-sm text-slate-700 hover:bg-white/50">Admin · Sessions</Link>
            <Link href="/settings" className="block px-3 py-2 text-sm text-slate-700 hover:bg-white/50">Settings</Link>
            <button className="w-full text-left px-3 py-2 text-sm text-slate-700 hover:bg-white/50">Language</button>
            <div className="h-px bg-white/30 my-1" />
            <button
              className="w-full text-left px-3 py-2 text-sm text-red-600 hover:bg-white/50"
              onClick={() => {
                try { setToken(null); } catch {}
                window.location.href = '/';
              }}
            >
              Log Out
            </button>
          </div>
        </div>, document.body)
      }
    </div>
  );
}
