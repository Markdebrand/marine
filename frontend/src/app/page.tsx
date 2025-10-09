import Link from "next/link";
import Image from "next/image";
import { Navbar } from "@/components/layout/Navbar";
import { Footer } from "@/components/layout/Footer";
import { Map, Search, Ship, BellRing, Database, Shield, Gauge, Network, Server, Play } from "lucide-react";

export default function Home() {
  return (
    <>
      <Navbar />
  <main className="container mx-auto px-6 sm:px-8 lg:px-12">
        {/* Hero mejorado */}
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
                Una plataforma. <span className="text-red-600">AIS</span> en <span className="text-red-600">tiempo real</span> para operaciones marítimas
              </h1>
              <p className="mt-4 text-slate-600 leading-relaxed">
                Mapa vivo, búsqueda por MMSI/IMO/nombre, ficha combinada, y gestión de favoritos/alertas.
                Arquitectura híbrida WSS + REST con bajos costos y cumplimiento de licencias.
              </p>
              <div className="mt-6 flex flex-wrap gap-3">
                <Link
                  href="/map"
                  className="inline-flex items-center gap-2 rounded-xl bg-red-600 px-6 py-3 text-white text-base font-medium shadow hover:bg-red-700"
                >
                  <Map className="h-5 w-5" /> Ver mapa en vivo
                </Link>
                <Link
                  href="/about"
                  className="inline-flex items-center gap-2 rounded-xl bg-white px-6 py-3 text-slate-800 text-base font-medium ring-1 ring-slate-200 hover:bg-slate-50"
                >
                  <Play className="h-5 w-5 text-red-600" /> Ver demo
                </Link>
              </div>
              <div className="mt-6 text-sm text-slate-500">
                Seguridad: JWT httpOnly + CSRF • HTTPS • CSP • Roles desde Odoo
              </div>
            </div>

            {/* panel visual derecho */}
            <div className="relative">
              <div className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-sky-50 via-white to-indigo-50 p-2 shadow-[0_10px_30px_rgba(2,6,23,0.08)] ring-1 ring-slate-200">
                <div className="relative aspect-[4/3] w-full overflow-hidden rounded-2xl">
                  <Image src="/Logo-2.png" alt="Marine Time" fill className="object-contain p-6" priority />
                  <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-white/0 via-white/0 to-white/0" />
                </div>
                <div className="absolute -right-10 -bottom-10 h-40 w-40 rounded-full bg-[rgba(239,68,68,0.18)] blur-[50px]" />
              </div>
            </div>
          </div>
        </section>

        {/* Qué puedes hacer */}
        <section className="py-12 border-t border-slate-200">
          <h2 className="text-xl sm:text-2xl font-semibold text-slate-900">Una plataforma. Capacidades clave</h2>
          <div className="mt-6 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
            {[{
              title: "Mapa en vivo",
              desc: "MapLibre GL (WebGL), marcadores rotados, clustering y mini-trayecto 6–12 h.",
              Icon: Map
            }, {
              title: "Búsqueda y ficha",
              desc: "Busca por MMSI/IMO/nombre. Ficha con estático enriquecido + último estado.",
              Icon: Search
            }, {
              title: "Favoritos y alertas",
              desc: "ABM de watchlist y alertas (geocerca/puerto) contra Odoo.",
              Icon: BellRing
            }, {
              title: "Puertos y eventos",
              desc: "Consulta UN/LOCODE y arribos/salidas si el proveedor lo soporta.",
              Icon: Ship
            }, {
              title: "Bajo costo y latencia",
              desc: "Stream WSS para posiciones y REST con cache TTL para enriquecimiento.",
              Icon: Gauge
            }, {
              title: "Seguridad",
              desc: "JWT httpOnly + CSRF, HTTPS, CSP estricta, roles desde Odoo.",
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

        {/* Arquitectura y métricas */}
        <section className="py-12 border-t border-slate-200">
          <div className="grid gap-6 lg:grid-cols-2">
            <div className="glass-card glass-hover p-6">
              <div className="text-sm font-medium text-slate-700">Arquitectura AIS Híbrida</div>
              <ul className="mt-3 space-y-3 text-slate-600">
                <li className="flex items-start gap-3"><Network className="mt-0.5 h-5 w-5 text-red-600" /><span>WSS/SSE para posiciones en vivo por BBOX y filtros.</span></li>
                <li className="flex items-start gap-3"><Server className="mt-0.5 h-5 w-5 text-red-600" /><span>FastAPI broker: normalización, cache TTL, geoprocesos, stream a la UI.</span></li>
                <li className="flex items-start gap-3"><Database className="mt-0.5 h-5 w-5 text-red-600" /><span>PostgreSQL + PostGIS + TimescaleDB para telemetría y tracks recientes.</span></li>
                <li className="flex items-start gap-3"><Shield className="mt-0.5 h-5 w-5 text-red-600" /><span>Odoo como SSoT: maestros, watchlist/alertas, auditoría, contratos.</span></li>
              </ul>
            </div>

            <div className="glass-card glass-hover p-6">
              <div className="text-sm font-medium text-slate-700">Métricas objetivo (MVP)</div>
              <ul className="mt-3 space-y-3 text-slate-600">
                <li>• Primer render del mapa &lt; 3 s • Actualizaciones &lt; 5 s desde WSS</li>
                <li>• Búsqueda (MMSI/IMO/nombre) &lt; 800 ms (cache caliente)</li>
                <li>• Ficha: estático (REST cache) + último estado (WSS/BD) + mini-trayecto</li>
                <li>• Watchlist/Alertas: CRUD en Odoo y triggers visibles en la UI</li>
              </ul>
            </div>
          </div>
        </section>

        {/* Roadmap breve y CTA */}
        <section className="py-12 border-t border-slate-200">
          <div className="rounded-2xl border border-slate-200 bg-white p-6">
            <h3 className="text-lg font-semibold text-slate-900">Roadmap inicial — siguiente entrega</h3>
            <p className="mt-2 text-slate-600">En la próxima fase nos centraremos en entregar capacidades operativas mínimas y validar con usuarios piloto.</p>
            <ul className="mt-4 list-disc list-inside text-slate-700 space-y-2">
              <li>Desplegar el stream en vivo en staging y validar latencia y reconexiones con datos reales.</li>
              <li>Implementar búsqueda y ficha de buque (cache local + enriquecimiento bajo demanda).</li>
              <li>Habilitar watchlist y alertas (geocerca/puerto) con CRUD sincronizado en Odoo.</li>
              <li>Instrumentar métricas clave (SSE/REST latency, reconexiones, consumo de proveedores).</li>
              <li>Ejecutar pruebas básicas de seguridad y preparar el despliegue con Docker Compose.</li>
            </ul>
            <div className="mt-4">
              <Link href="/contact" className="inline-flex items-center rounded-lg border border-red-600 bg-red-50 px-4 py-2 text-red-700 font-medium hover:bg-red-100">
                Solicitar acceso beta
              </Link>
            </div>
          </div>
        </section>
      </main>
      <Footer />
    </>
  );
}
