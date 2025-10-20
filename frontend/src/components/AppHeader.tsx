"use client";
import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";

export default function AppHeader() {
  const pathname = usePathname();
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

  return (
    <div className={containerClass}>
      <div className="mx-auto max-w-7xl px-6">
        <div className="glass-card flex items-center justify-between gap-4 p-3 border border-white/30 shadow-[0_10px_30px_rgba(2,6,23,0.06)] backdrop-blur-md">
          <div className="flex items-center gap-3">
            <Image src="/Icon.png" alt="MarinaLive" width={28} height={28} className="h-7 w-7" />
            <span className="font-semibold text-slate-900">HSO Marine</span>
          </div>
          <nav className="flex items-center gap-2">
            {link("/dashboard", "Dashboard")}
            {link("/map", "Live Map")}
            {link("/watchlist", "Watchlist")}
          </nav>
        </div>
      </div>
    </div>
  );
}
