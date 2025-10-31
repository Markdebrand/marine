import Image from "next/image";
import {
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  Gauge,
  Scale,
} from "lucide-react";

export default function ServicesPage() {
  return (
    <section className="container mx-auto px-6 sm:px-8 lg:px-12 py-12">
      {/* Hero distribuido con imagen */}
      <div className="py-4">
        <div className="grid md:grid-cols-2 gap-8 items-center">
          <div>
            <h1 className="text-3xl sm:text-4xl font-semibold tracking-tight text-slate-900">
              Servicios
            </h1>
            <div className="mt-2 h-1 w-24 rounded-full bg-linear-to-r from-red-600 to-rose-400" />
            <p className="mt-4 text-slate-700 leading-relaxed">
              Información de servicio: SLOs, cuotas, políticas de datos,
              seguridad, integración y operación.
            </p>
            <div className="mt-6">
              <a
                href="#modules"
                className="inline-flex items-center rounded-md bg-red-600 px-5 py-3 text-white text-sm font-medium hover:bg-red-700"
              >
                Ver módulos
              </a>
            </div>
          </div>
          <div className="rounded-2xl overflow-hidden shadow-sm">
            <div className="relative aspect-4/3 w-full overflow-hidden">
              <Image
                src="/images/servicios2webp.webp"
                alt="Servicios"
                fill
                className="object-cover"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Sección overlay con tarjeta y flechas */}
      <div
        id="modules"
        className="mt-10 relative rounded-2xl overflow-hidden"
        style={{
          background:
            "linear-gradient(135deg, rgba(239,68,68,0.08), rgba(244,63,94,0.08))",
        }}
      >
        <div className="absolute inset-0 -z-10">
          <div className="h-full w-full bg-[radial-gradient(1000px_400px_at_70%_30%,rgba(255,255,255,0.5),transparent)]" />
        </div>
        <div className="p-6 md:p-10">
          <div className="flex items-center justify-between text-slate-900/70">
            <div className="text-xl sm:text-2xl font-semibold">
              Módulo operativo
            </div>
            <div className="flex gap-2">
              <button className="inline-flex h-9 w-9 items-center justify-center rounded-full bg-white/70 ring-1 ring-slate-200 hover:bg-white">
                <ArrowLeft className="h-4 w-4" />
              </button>
              <button className="inline-flex h-9 w-9 items-center justify-center rounded-full bg-white/70 ring-1 ring-slate-200 hover:bg-white">
                <ArrowRight className="h-4 w-4" />
              </button>
            </div>
          </div>
          <div className="mt-4 glass-card p-6">
            <div className="text-slate-900 font-semibold">SLOs por dominio</div>
            <div className="mt-3 flex flex-col divide-y divide-slate-200">
              {[
                {
                  title: "Live stream (SSE)",
                  defs: [
                    {
                      k: "Latencia",
                      v: "< 5 s — tiempo esperado desde ingestión hasta entrega al cliente en condiciones normales.",
                    },
                    {
                      k: "Disponibilidad",
                      v: "99.5% objetivo — medida sobre ventanas mensuales; mantenimiento planificado excluido.",
                    },
                    {
                      k: "Resiliencia",
                      v: "Reintentos con backoff y heartbeats — reconexión automática y detección de stalls para minimizar pérdidas de eventos.",
                    },
                  ],
                },
                {
                  title: "Lecturas REST (vessels/ports)",
                  defs: [
                    {
                      k: "P95 caliente",
                      v: "< 800 ms — respuesta cuando el recurso está en cache; objetivo para tráfico operativo.",
                    },
                    {
                      k: "TTL",
                      v: "Estáticos 24–72 h; puertos 1–6 h — políticas de frescura que balancean coste y actualidad.",
                    },
                    {
                      k: "Rate-limit",
                      v: "Por usuario/IP — protección contra abuso (códigos 429) y mecanismos de auditoría.",
                    },
                  ],
                },
                {
                  title: "Persistencia operativa",
                  defs: [
                    {
                      k: "Tecnología",
                      v: "Postgres + PostGIS + Timescale — diseñada para series temporales y consultas geoespaciales.",
                    },
                    {
                      k: "Retención",
                      v: "≤ N días — configuración por contrato; compresión y eliminación automática de chunks antiguos.",
                    },
                    {
                      k: "Índices",
                      v: "GiST para geom y compuestos (mmsi, ts DESC) para consultas eficientes.",
                    },
                  ],
                },
              ].map((b, i) => (
                <section key={i} className="py-4">
                  <div className="flex gap-4 items-start">
                    <div className="shrink-0">
                      <Gauge className="h-5 w-5 text-red-600" />
                    </div>
                    <div className="w-full">
                      <div className="text-slate-900 font-semibold">
                        {b.title}
                      </div>
                      <dl className="mt-2 text-sm text-slate-700">
                        {b.defs.map((d, j) => (
                          <div
                            key={j}
                            className="grid grid-cols-[120px_1fr] gap-2 py-1"
                          >
                            <dt className="text-slate-500">{d.k}</dt>
                            <dd>{d.v}</dd>
                          </div>
                        ))}
                      </dl>
                    </div>
                  </div>
                </section>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Grid de 3 tarjetas (cuotas y límites) */}
      <div className="mt-10">
        <div className="text-center">
          <div className="text-2xl font-semibold text-slate-900">
            Cuotas y límites
          </div>
          <div className="mx-auto mt-2 h-1 w-20 rounded-full bg-gradient-to-r from-red-600 to-rose-400" />
        </div>
        <div className="mt-6 grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {[
            {
              title: "Stream SSE",
              defs: [
                {
                  k: "BBOX",
                  v: "Máximo por solicitud (configurable) — limita el área para proteger latencia y coste.",
                },
                {
                  k: "Mensajes",
                  v: "Tipos soportados según dominio — p.ej. posiciones AIS posicionales; otros tipos filtrables.",
                },
                {
                  k: "Sesiones",
                  v: "Conexiones simultáneas por usuario — políticas de fair-use y límites por plan.",
                },
              ],
            },
            {
              title: "Enrichment REST",
              defs: [
                {
                  k: "QPS",
                  v: "Por endpoint (según plan) — medido y aplicado; excedentes retornan 429.",
                },
                {
                  k: "TTL",
                  v: "Por dominio — define frescura frente a coste de proveedores.",
                },
                {
                  k: "Backoff",
                  v: "Estrategia exponencial ante 5xx/429 del proveedor para proteger colas y costos.",
                },
              ],
            },
            {
              title: "Datos y retención",
              defs: [
                {
                  k: "Retención",
                  v: "Operativa ≤ N días — periodo configurable por contrato; históricas profundas fuera del alcance MVP.",
                },
                {
                  k: "Compresión",
                  v: "Compresión en caliente para reducir costes de almacenamiento sin afectar consultas recientes.",
                },
                {
                  k: "Exportación",
                  v: "Sujeta a política de licencia — exportaciones y redistribución controladas por acuerdos con proveedores.",
                },
              ],
            },
          ].map((b, i) => (
            <div key={i} className="p-4">
              <div className="flex items-center gap-2 text-slate-900 font-semibold">
                <Scale className="h-5 w-5 text-red-600" /> {b.title}
              </div>
              <dl className="mt-2 text-sm text-slate-700">
                {b.defs.map((d, j) => (
                  <div
                    key={j}
                    className="grid grid-cols-[120px_1fr] gap-2 py-1"
                  >
                    <dt className="text-slate-500">{d.k}</dt>
                    <dd>{d.v}</dd>
                  </div>
                ))}
              </dl>
            </div>
          ))}
        </div>
      </div>

      {/* Nota sobre políticas */}
      <div className="mt-10 section-surface">
        <div className="text-sm font-medium text-slate-700">
          Políticas de servicio
        </div>
        <p className="mt-3 text-sm text-slate-700">
          Los límites de cuota, cache y retención se rigen por contrato de
          proveedor y plan vigente. Cambios pueden requerir actualización de
          políticas y auditoría.
        </p>
      </div>

      {/* Bloque de pasos (flujo de servicio) */}
      <div className="mt-10">
        <div className="text-center">
          <div className="text-2xl font-semibold text-slate-900">
            Flujo de servicio
          </div>
          <div className="mx-auto mt-2 h-1 w-24 rounded-full bg-gradient-to-r from-red-600 to-rose-400" />
        </div>
        <div className="mt-6 max-w-3xl mx-auto rounded-2xl border border-slate-200 bg-white p-6">
          <ol className="space-y-3 text-slate-700 text-sm">
            <li className="flex gap-3">
              <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-red-600 text-white text-xs font-semibold">
                1
              </span>{" "}
              Definir dominios y cuotas por plan.
            </li>
            <li className="flex gap-3">
              <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-red-600 text-white text-xs font-semibold">
                2
              </span>{" "}
              Establecer SLOs y métricas de observabilidad.
            </li>
            <li className="flex gap-3">
              <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-red-600 text-white text-xs font-semibold">
                3
              </span>{" "}
              Configurar políticas de cache, retención y rate-limit.
            </li>
            <li className="flex gap-3">
              <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-red-600 text-white text-xs font-semibold">
                4
              </span>{" "}
              Publicar endpoints y versionado.
            </li>
            <li className="flex gap-3">
              <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-red-600 text-white text-xs font-semibold">
                5
              </span>{" "}
              Monitorear consumo y ajustar parámetros.
            </li>
          </ol>
        </div>
      </div>

      {/* Cierre con imagen + bullets */}
      <div className="mt-10 grid md:grid-cols-2 gap-8 items-center">
        <div className="rounded-2xl overflow-hidden shadow-sm">
          <div className="relative aspect-4/3 w-full overflow-hidden">
            <Image
              src="/images/contact2webp.webp"
              alt="Resumen"
              fill
              className="object-cover"
            />
          </div>
        </div>
        <div>
          <div className="text-2xl font-semibold text-slate-900">
            Gobierno y operación
          </div>
          <dl className="mt-4 text-sm text-slate-700">
            {[
              { k: "Seguridad", v: "Aplicativa y auditoría centralizada" },
              {
                k: "Integración",
                v: "DTOs por proveedor y políticas de rate-limit",
              },
              { k: "Observabilidad", v: "Métricas y salud por módulo" },
            ].map((d, i) => (
              <div key={i} className="grid grid-cols-[120px_1fr] gap-2 py-1">
                <dt className="flex items-center gap-2 text-slate-500">
                  <CheckCircle2 className="h-4 w-4 text-green-600" /> {d.k}
                </dt>
                <dd>{d.v}</dd>
              </div>
            ))}
          </dl>
          <div className="mt-6">
            <a
              href="#modules"
              className="inline-flex items-center rounded-md border px-5 py-3 text-sm font-medium"
            >
              Ver módulos
            </a>
          </div>
        </div>
      </div>
      {/* Conceptos clave */}
      <div className="mt-12 section-surface">
        <div className="text-2xl font-semibold text-slate-900">
          Conceptos clave
        </div>
        <div className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3 text-sm text-slate-700">
          {[
            {
              term: "AIS (Automatic Identification System)",
              desc: "Sistema de transmisión de posiciones y datos de buques; base para la telemetría en tiempo real.",
            },
            {
              term: "WSS",
              desc: "WebSocket Secure: conexión bidireccional segura para streaming de datos de baja latencia.",
            },
            {
              term: "SSE (Server-Sent Events)",
              desc: "Mecanismo de stream unidireccional desde servidor a cliente; sencillo y robusto para MVP.",
            },
            {
              term: "BBOX",
              desc: "Bounding box geográfica (minLon,minLat,maxLon,maxLat) usada para filtrar streams por área.",
            },
            {
              term: "DTO (Data Transfer Object)",
              desc: "Estructura de datos estándar para abstraer respuestas de distintos proveedores.",
            },
            {
              term: "SLO (Service Level Objective)",
              desc: "Objetivo medible de servicio (latencia, disponibilidad) que guía los SLAs.",
            },
            {
              term: "TTL (Time To Live)",
              desc: "Tiempo de vida de una entrada en cache antes de considerarla obsoleta.",
            },
            {
              term: "PostGIS",
              desc: "Extensión espacial de PostgreSQL para manejo de geometrías y consultas geoespaciales.",
            },
            {
              term: "TimescaleDB",
              desc: "Extensión para PostgreSQL optimizada para series temporales (alta ingestión y compresión).",
            },
            {
              term: "GiST",
              desc: "Tipo de índice para datos espaciales usado en PostGIS para búsquedas eficientes.",
            },
            {
              term: "Geofence",
              desc: "Área geográfica definida para detectar entradas y salidas (alertas).",
            },
            {
              term: "UN/LOCODE",
              desc: "Código estandarizado de localización de puertos usado como identificador único.",
            },
            {
              term: "Rate-limit",
              desc: "Límite de peticiones por segundo/usuario para proteger servicios y proveedores.",
            },
            {
              term: "Backoff",
              desc: "Estrategia de reintentos exponencial para reducir la presión sobre proveedores tras errores o límites.",
            },
          ].map((c, i) => (
            <div key={i} className="glass-card p-4">
              <div className="font-semibold text-slate-900">{c.term}</div>
              <div className="mt-1 text-slate-700 text-sm">{c.desc}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
