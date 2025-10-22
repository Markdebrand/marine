import Image from "next/image";
import { CheckCircle2, Shield, Zap, Map, BellRing, Search, ArrowRight } from "lucide-react";

export default function AboutPage() {
  return (
    <section className="container mx-auto px-6 sm:px-8 lg:px-12 py-12">
      {/* Short, customer-oriented hero */}
  <div className="relative overflow-visible section-surface">
        {/* decor */}
        <div className="pointer-events-none absolute left-1/2 top-1/2 -z-10 h-[130%] w-[130%] -translate-x-1/2 -translate-y-1/2">
          <div className="absolute -top-[18%] -left-[22%] h-80 w-80 rounded-full bg-[rgba(239,68,68,0.16)] blur-[54px]" />
          <div className="absolute -bottom-[18%] -right-[22%] h-80 w-80 rounded-full bg-[rgba(99,102,241,0.14)] blur-[54px]" />
        </div>

        <div className="grid gap-8 md:grid-cols-2 items-stretch">
          <div className="flex flex-col justify-center">
            <h1 className="text-3xl sm:text-4xl font-semibold tracking-tight text-slate-900">
              About Marine Time
            </h1>
            <div className="mt-2 h-1 w-20 rounded-full bg-linear-to-r from-red-600 to-rose-400" />
            <p className="mt-4 text-slate-700 leading-relaxed">
              A simple platform to view maritime traffic in real time and make quick decisions.
              Designed for operations and commercial teams that need visibility, context, and alerts without complexity.
            </p>
          </div>
          <div className="glass-card p-3 sm:p-4">
            <div className="relative aspect-4/3 w-full overflow-hidden rounded-2xl bg-linear-to-br from-sky-50 via-white to-indigo-50">
              <Image src="/HSOMarineLogo.svg" alt="Marine Time" fill className="object-contain p-6" />
            </div>
          </div>
        </div>
      </div>

      {/* What you get */}
  <div className="mt-10 section-surface">
        <div className="text-sm font-medium text-slate-700">What you get</div>
        <ul className="mt-3 grid gap-4 sm:grid-cols-2 text-slate-700 text-sm">
          <li className="flex items-start gap-3">
            <span className="inline-flex h-8 w-8 items-center justify-center rounded-lg bg-red-50 ring-1 ring-red-200"><Zap className="h-4 w-4 text-red-600" /></span>
            <span>Live updates on the map with a responsive interface.</span>
          </li>
          <li className="flex items-start gap-3">
            <span className="inline-flex h-8 w-8 items-center justify-center rounded-lg bg-red-50 ring-1 ring-red-200"><Search className="h-4 w-4 text-red-600" /></span>
            <span>Search by MMSI/IMO/name and a clear vessel profile.</span>
          </li>
          <li className="flex items-start gap-3">
            <span className="inline-flex h-8 w-8 items-center justify-center rounded-lg bg-red-50 ring-1 ring-red-200"><BellRing className="h-4 w-4 text-red-600" /></span>
            <span>Favorites and alerts by geofence/port to be notified in time.</span>
          </li>
          <li className="flex items-start gap-3">
            <span className="inline-flex h-8 w-8 items-center justify-center rounded-lg bg-red-50 ring-1 ring-red-200"><Shield className="h-4 w-4 text-red-600" /></span>
            <span>Security and licensing: governed data with privacy and control.</span>
          </li>
        </ul>
      </div>

      {/* User benefits (non-technical) */}
  <div className="mt-10 grid gap-6 lg:grid-cols-3 section-surface">
        {[{
          title: "Real visibility",
          desc: "Track vessels live and detect changes without waiting for reports.",
          Icon: Map
        }, {
          title: "Fast decisions",
          desc: "Fewer clicks, more context: direct profile and unified search.",
          Icon: Zap
        }, {
          title: "Useful alerts",
          desc: "Define geofences or ports and receive timely notifications.",
          Icon: BellRing
        }].map(({ title, desc, Icon }, i) => (
          <div key={i} className="glass-card p-6 transition-transform duration-200 hover:-translate-y-1">
            <div className="flex items-center gap-2 text-slate-900 font-semibold">
              <Icon className="h-5 w-5 text-red-600" /> {title}
            </div>
            <p className="mt-2 text-slate-700 text-sm">{desc}</p>
          </div>
        ))}
      </div>

      {/* Trust and compliance */}
  <div className="mt-10 section-surface">
        <div className="text-sm font-medium text-slate-700">Trust and compliance</div>
        <ul className="mt-3 grid gap-4 sm:grid-cols-2 text-slate-700 text-sm">
          {["Access with control and privacy; secure session.", "Data with proper licensing and retention.", "High availability; support for teams in operation.", "Gradual evolution without friction for users."].map((t, i) => (
            <li key={i} className="relative pl-4">
              <span className="absolute left-0 top-2 h-8 w-[3px] rounded-full bg-linear-to-b from-green-500 to-emerald-400" />
              <span className="inline-flex items-start gap-2"><CheckCircle2 className="mt-0.5 h-5 w-5 text-green-600" /> {t}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Short FAQ */}
      <div className="mt-10 grid gap-6 md:grid-cols-2">
        <div className="glass-card p-6">
          <div className="font-semibold text-slate-900">Do I need training?</div>
          <p className="mt-2 text-slate-700 text-sm">No. The interface is straightforward: open the map, search a vessel, or mark your favorites. You’ll be operating in minutes.</p>
        </div>
        <div className="glass-card p-6">
          <div className="font-semibold text-slate-900">What alerts are supported?</div>
          <p className="mt-2 text-slate-700 text-sm">Geofence entry/exit and port notifications. We’ll add more types based on user priorities.</p>
        </div>
      </div>

      {/* CTA */}
  <div className="mt-10 rounded-2xl p-1 bg-linear-to-r from-red-500 to-rose-400 section-surface">
        <div className="glass-card flex items-center justify-between gap-4 p-6">
          <div>
            <div className="text-slate-900 font-semibold">Ready to try it?</div>
            <p className="text-slate-700 text-sm">Request beta access or explore the map if you already have credentials.</p>
          </div>
          <a href="/map" className="inline-flex items-center rounded-xl bg-red-600 px-5 py-3 text-white text-sm font-medium hover:bg-red-700">
            Go to map <ArrowRight className="ml-2 h-4 w-4" />
          </a>
        </div>
      </div>
    </section>
  );
}
