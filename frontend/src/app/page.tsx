import Link from "next/link";
import Image from "next/image";
import { Navbar } from "@/app/(home)/components/Navbar";
import { Footer } from "@/app/(home)/components/Footer";
import { Map, Search, Ship, BellRing, Database, Shield, Gauge, Network, Server, Play } from "lucide-react";

export default function Home() {
  return (
    <>
      <Navbar />
  <main className="container mx-auto px-6 sm:px-8 lg:px-12">
        {/* Enhanced hero */}
        <section className="relative overflow-visible py-14 sm:py-20">
          {/* decor — expand beyond container to avoid clipping */}
          <div className="pointer-events-none absolute left-1/2 top-1/2 -z-10 h-[140%] w-[140%] -translate-x-1/2 -translate-y-1/2">
            <div className="absolute -top-[20%] -left-[25%] h-96 w-96 rounded-full bg-[rgba(239,68,68,0.18)] blur-[60px]" />
            <div className="absolute -bottom-[20%] -right-[25%] h-96 w-96 rounded-full bg-[rgba(99,102,241,0.16)] blur-[60px]" />
          </div>

          <div className="grid items-center gap-10 md:grid-cols-2">
            <div>
              <span className="inline-flex items-center rounded-full bg-red-50 px-3 py-1 text-xs font-medium text-red-700 ring-1 ring-red-200">MVP • Odoo SSoT</span>
              <h1 className="mt-3 text-3xl sm:text-5xl font-semibold tracking-tight text-slate-900">
                One platform. <span className="text-red-600">AIS</span> in <span className="text-red-600">real time</span> for maritime operations
              </h1>
              <p className="mt-4 text-slate-600 leading-relaxed">
                Live map, search by MMSI/IMO/name, unified vessel profile, and favorites/alerts management.
                Hybrid WSS + REST architecture with low cost and license compliance.
              </p>
              <div className="mt-6 flex flex-wrap gap-3">
                <Link
                  href="/map"
                  className="inline-flex items-center gap-2 rounded-xl bg-red-600 px-6 py-3 text-white text-base font-medium shadow hover:bg-red-700"
                >
                  <Map className="h-5 w-5" /> View live map
                </Link>
                <Link
                  href="/about"
                  className="inline-flex items-center gap-2 rounded-xl bg-white px-6 py-3 text-slate-800 text-base font-medium ring-1 ring-slate-200 hover:bg-slate-50"
                >
                  <Play className="h-5 w-5 text-red-600" /> View demo
                </Link>
              </div>
              <div className="mt-6 text-sm text-slate-500">
                Security: httpOnly JWT + CSRF • HTTPS • CSP • Roles from Odoo
              </div>
            </div>

            {/* right visual panel */}
            <div className="relative">
              <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-sky-50 via-white to-indigo-50 p-2 shadow-[0_10px_30px_rgba(2,6,23,0.08)] ring-1 ring-slate-200">
                <div className="relative aspect-[4/3] w-full overflow-hidden rounded-2xl">
                  <Image src="/HSO Marine Isotype.svg" alt="Marine Time" fill className="object-contain p-6" priority />
                  <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-white/0 via-white/0 to-white/0" />
                </div>
                <div className="absolute -right-10 -bottom-10 h-40 w-40 rounded-full bg-[rgba(239,68,68,0.18)] blur-[50px]" />
              </div>
            </div>
          </div>
        </section>

        {/* What you can do */}
        <section className="py-12 border-t border-slate-200">
          <h2 className="text-xl sm:text-2xl font-semibold text-slate-900">One platform. Key capabilities</h2>
          <div className="mt-6 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {[{
              title: "Live map",
              desc: "MapLibre GL (WebGL), rotated markers, clustering, and 6–12h mini-track.",
              Icon: Map
            }, {
              title: "Search & profile",
              desc: "Search by MMSI/IMO/name. Profile with enriched static data + last position.",
              Icon: Search
            }, {
              title: "Favorites & alerts",
              desc: "CRUD for watchlist and alerts (geofence/port) synchronized with Odoo.",
              Icon: BellRing
            }, {
              title: "Ports & events",
              desc: "Query UN/LOCODE and arrivals/departures when the provider supports it.",
              Icon: Ship
            }, {
              title: "Low cost & latency",
              desc: "WSS stream for positions and REST with TTL cache for enrichment.",
              Icon: Gauge
            }, {
              title: "Security",
              desc: "httpOnly JWT + CSRF, HTTPS, strict CSP, roles from Odoo.",
              Icon: Shield
            }].map(({ title, desc, Icon }, i) => (
              <div key={i} className="relative glass-card glass-hover p-6">
                <div className="absolute -right-3 -top-3 h-12 w-12 rounded-full bg-red-100" />
                <div className="relative flex items-center gap-2 text-slate-900 font-medium">
                  <Icon className="h-5 w-5 text-red-600" /> {title}
                </div>
                <p className="relative mt-2 text-slate-600 text-sm leading-relaxed">{desc}</p>
              </div>
            ))}
          </div>
        </section>

        {/* Architecture & metrics */}
        <section className="py-12 border-t border-slate-200">
          <div className="grid gap-6 lg:grid-cols-2">
            <div className="glass-card glass-hover p-6">
              <div className="text-sm font-medium text-slate-700">Hybrid AIS Architecture</div>
              <ul className="mt-3 space-y-3 text-slate-600">
                <li className="flex items-start gap-3"><Network className="mt-0.5 h-5 w-5 text-red-600" /><span>WSS/SSE for live positions by BBOX and filters.</span></li>
                <li className="flex items-start gap-3"><Server className="mt-0.5 h-5 w-5 text-red-600" /><span>FastAPI broker: normalization, TTL cache, geoprocessing, and UI stream.</span></li>
                <li className="flex items-start gap-3"><Database className="mt-0.5 h-5 w-5 text-red-600" /><span>PostgreSQL + PostGIS + TimescaleDB for telemetry and recent tracks.</span></li>
                <li className="flex items-start gap-3"><Shield className="mt-0.5 h-5 w-5 text-red-600" /><span>Odoo as SSoT: masters, watchlist/alerts, auditing, contracts.</span></li>
              </ul>
            </div>

            <div className="glass-card glass-hover p-6">
              <div className="text-sm font-medium text-slate-700">Target metrics (MVP)</div>
              <ul className="mt-3 space-y-3 text-slate-600">
                <li>• First map render &lt; 3 s • Updates &lt; 5 s from WSS</li>
                <li>• Search (MMSI/IMO/name) &lt; 800 ms (warm cache)</li>
                <li>• Profile: static (REST cache) + last state (WSS/DB) + mini-track</li>
                <li>• Watchlist/Alerts: CRUD in Odoo and triggers visible in the UI</li>
              </ul>
            </div>
          </div>
        </section>

        {/* Short roadmap & CTA */}
        <section className="py-12 border-t border-slate-200">
          <div className="rounded-2xl border border-slate-200 bg-white p-6">
            <h3 className="text-lg font-semibold text-slate-900">Initial roadmap — next delivery</h3>
            <p className="mt-2 text-slate-600">In the next phase we will focus on delivering minimum operational capabilities and validating with pilot users.</p>
            <ul className="mt-4 list-disc list-inside text-slate-700 space-y-2">
              <li>Deploy live stream on staging and validate latency and reconnections with real data.</li>
              <li>Implement vessel search and profile (local cache + on-demand enrichment).</li>
              <li>Enable watchlist and alerts (geofence/port) with CRUD synchronized with Odoo.</li>
              <li>Instrument key metrics (SSE/REST latency, reconnects, provider consumption).</li>
              <li>Run basic security tests and prepare deployment with Docker Compose.</li>
            </ul>
            <div className="mt-4">
              <Link href="/contact" className="inline-flex items-center rounded-lg border border-red-600 bg-red-50 px-4 py-2 text-red-700 font-medium hover:bg-red-100">
                Request beta access
              </Link>
            </div>
          </div>
        </section>
      </main>
      <Footer />
    </>
  );
}
