"use client";
import { useEffect, useState } from "react";
import { Protected } from "@/components/auth/Protected";
import {
  Activity,
  Bell,
  ListChecks,
  Map as MapIcon,
  Settings,
  BookMarked,
  Search,
  PlusCircle,
} from "lucide-react";

type Health = "loading" | "ok" | "warn" | "down";

export default function DashboardPage() {
  const [loading, setLoading] = useState(true);
  const [healthError, setHealthError] = useState<string | null>(null);
  const [metrics, setMetrics] = useState({
    vesselsLive: 0,
    inView: 0,
    watchlist: 0,
    alerts: 0,
  });

  useEffect(() => {
    const t = setTimeout(() => {
      // Simulate metrics loaded and a health fetch failure like in the image
      setMetrics({
        vesselsLive: 124_530,
        inView: 382,
        watchlist: 6,
        alerts: 2,
      });
      setHealthError("Failed to fetch");
      setLoading(false);
    }, 700);
    return () => clearTimeout(t);
  }, []);

  return (
    <Protected>
      <main className="py-2">
        {/* Header */}
        <header className="py-6">
          <div className="glass-card glass-hover p-6 relative">
            <div className="absolute -right-6 -top-6 h-24 w-24 rounded-full bg-[rgba(239,68,68,0.12)] blur-[40px]" />
            <div className="flex items-center justify-between">
              <div>
                <h1 className="text-3xl font-semibold text-slate-900">
                  Dashboard
                </h1>
                <p className="text-slate-600 mt-1">
                  Welcome back. Choose where to start.
                </p>
              </div>
              <div className="flex items-center gap-3">
                <a
                  href="/map"
                  className="inline-flex items-center gap-2 rounded-xl bg-red-600 px-4 py-2 text-white text-sm font-medium shadow hover:bg-red-700"
                >
                  Open live map
                </a>
                <a
                  href="/services"
                  className="inline-flex items-center gap-2 rounded-xl bg-white px-4 py-2 text-slate-800 text-sm font-medium ring-1 ring-slate-200 hover:bg-slate-50"
                >
                  Services
                </a>
              </div>
            </div>
          </div>
        </header>

        {/* Feature cards (3) */}
        <section className="mt-6 grid gap-6 md:grid-cols-3">
          <FeatureCard
            title="Live Map"
            description="See real-time AIS positions."
            href="/map"
            cta="Open map"
            icon={<MapIcon className="h-4 w-4" />}
          />
          <FeatureCard
            title="Watchlist"
            description="Manage your favorite vessels."
            href="/watchlist"
            cta="Open watchlist"
            icon={<ListChecks className="h-4 w-4" />}
          />
          <FeatureCard
            title="Service Catalog"
            description="SLOs, quotas, policies and glossary."
            href="/services"
            cta="View services"
            icon={<BookMarked className="h-4 w-4" />}
          />
        </section>


      </main>
    </Protected>
  );
}

function HealthPill({ state }: { state: Health }) {
  const cfg: Record<
    Exclude<Health, "loading">,
    { text: string; cls: string }
  > = {
    ok: { text: "OK", cls: "bg-green-50 text-green-700 ring-green-200" },
    warn: { text: "WARN", cls: "bg-yellow-50 text-yellow-700 ring-yellow-200" },
    down: { text: "DOWN", cls: "bg-red-50 text-red-700 ring-red-200" },
  };
  if (state === "loading")
    return (
      <span className="inline-block h-6 w-20 rounded bg-slate-100 animate-pulse" />
    );
  const { text, cls } = cfg[state];
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-semibold ring-1 ${cls}`}
    >
      {text}
    </span>
  );
}

function MetricTile({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value?: string;
}) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-4">
      <div className="flex items-center gap-2 text-slate-500 text-sm">
        {icon} {label}
      </div>
      {value ? (
        <div className="mt-2 text-2xl font-semibold text-slate-900">
          {value}
        </div>
      ) : (
        <div className="mt-2 h-8 w-24 rounded bg-slate-100 animate-pulse" />
      )}
    </div>
  );
}

function FeatureCard({
  title,
  description,
  href,
  cta,
  icon,
}: {
  title: string;
  description: string;
  href: string;
  cta: string;
  icon: React.ReactNode;
}) {
  return (
    <a href={href} className="block glass-card glass-hover p-6">
      <div className="relative flex items-start justify-between">
        <div className="absolute -right-3 -top-3 h-10 w-10 rounded-full bg-red-100" />
        <div>
          <div className="text-slate-900 font-semibold">{title}</div>
          <p className="text-sm text-slate-600 mt-1">{description}</p>
        </div>
        <div className="text-slate-400">{icon}</div>
      </div>
      <div className="mt-4 inline-flex items-center gap-1 text-sm text-red-600 px-3 py-1.5 rounded-md border border-red-200 hover:bg-red-50">
        {cta} <span aria-hidden>→</span>
      </div>
    </a>
  );
}

function ActionCard({
  icon,
  title,
  description,
  href,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
  href: string;
}) {
  return (
    <a
      href={href}
      className="block rounded-xl border border-slate-200 bg-white p-5 hover:shadow-sm transition-shadow"
    >
      <div className="flex items-center gap-3 text-slate-900 font-semibold">
        {icon}
        <span>{title}</span>
      </div>
      <p className="text-sm text-slate-600 mt-1">{description}</p>
    </a>
  );
}
