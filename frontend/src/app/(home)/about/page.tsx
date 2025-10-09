import Image from "next/image";
import { CheckCircle2, Shield, Zap, Map, BellRing, Search, ArrowRight } from "lucide-react";

export default function AboutPage() {
  return (
    <section className="container mx-auto px-6 sm:px-8 lg:px-12 py-12">
      {/* Hero breve y orientado al cliente */}
  <div className="relative overflow-visible section-surface">
        {/* decor */}
        <div className="pointer-events-none absolute left-1/2 top-1/2 -z-10 h-[130%] w-[130%] -translate-x-1/2 -translate-y-1/2">
          <div className="absolute -top-[18%] -left-[22%] h-80 w-80 rounded-full bg-[rgba(239,68,68,0.16)] blur-[54px]" />
          <div className="absolute -bottom-[18%] -right-[22%] h-80 w-80 rounded-full bg-[rgba(99,102,241,0.14)] blur-[54px]" />
        </div>

        <div className="grid gap-8 md:grid-cols-2 items-stretch">
          <div className="flex flex-col justify-center">
            <h1 className="text-3xl sm:text-4xl font-semibold tracking-tight text-slate-900">
              Sobre Marine Time
            </h1>
            <div className="mt-2 h-1 w-20 rounded-full bg-gradient-to-r from-red-600 to-rose-400" />
            <p className="mt-4 text-slate-700 leading-relaxed">
              Una plataforma sencilla para ver tráfico marítimo en tiempo real y tomar decisiones rápidas.
              Pensada para equipos operativos y comerciales que necesitan visibilidad, contexto y alertas sin complejidad.
            </p>
          </div>
          <div className="glass-card p-3 sm:p-4">
            <div className="relative aspect-[4/3] w-full overflow-hidden rounded-2xl bg-gradient-to-br from-sky-50 via-white to-indigo-50">
              <Image src="/Logo-2.png" alt="Marine Time" fill className="object-contain p-6" />
            </div>
          </div>
        </div>
      </div>

      {/* Lo que te llevas */}
  <div className="mt-10 section-surface">
        <div className="text-sm font-medium text-slate-700">Lo que te llevas</div>
        <ul className="mt-3 grid gap-4 sm:grid-cols-2 text-slate-700 text-sm">
          <li className="flex items-start gap-3">
            <span className="inline-flex h-8 w-8 items-center justify-center rounded-lg bg-red-50 ring-1 ring-red-200"><Zap className="h-4 w-4 text-red-600" /></span>
            <span>Actualizaciones en vivo en el mapa con una interfaz ágil.</span>
          </li>
          <li className="flex items-start gap-3">
            <span className="inline-flex h-8 w-8 items-center justify-center rounded-lg bg-red-50 ring-1 ring-red-200"><Search className="h-4 w-4 text-red-600" /></span>
            <span>Búsqueda por MMSI/IMO/nombre y ficha clara por buque.</span>
          </li>
          <li className="flex items-start gap-3">
            <span className="inline-flex h-8 w-8 items-center justify-center rounded-lg bg-red-50 ring-1 ring-red-200"><BellRing className="h-4 w-4 text-red-600" /></span>
            <span>Favoritos y alertas por geocerca/puerto para enterarte a tiempo.</span>
          </li>
          <li className="flex items-start gap-3">
            <span className="inline-flex h-8 w-8 items-center justify-center rounded-lg bg-red-50 ring-1 ring-red-200"><Shield className="h-4 w-4 text-red-600" /></span>
            <span>Seguridad y licencias: datos con gobierno, privacidad y control.</span>
          </li>
        </ul>
      </div>

      {/* Beneficios para el usuario (sin tecnicismos) */}
  <div className="mt-10 grid gap-6 lg:grid-cols-3 section-surface">
        {[{
          title: "Visibilidad real",
          desc: "Sigue buques en vivo y detecta cambios sin esperar reportes.",
          Icon: Map
        }, {
          title: "Decisiones rápidas",
          desc: "Menos clics, más contexto: ficha directa y búsqueda unificada.",
          Icon: Zap
        }, {
          title: "Alertas útiles",
          desc: "Define geocercas o puertos y recibe avisos oportunos.",
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

      {/* Confianza y cumplimiento */}
  <div className="mt-10 section-surface">
        <div className="text-sm font-medium text-slate-700">Confianza y cumplimiento</div>
        <ul className="mt-3 grid gap-4 sm:grid-cols-2 text-slate-700 text-sm">
          {["Acceso con control y privacidad; sesión segura.", "Datos con licencias y retención adecuadas.", "Alta disponibilidad; soporte para equipos en operación.", "Evolución gradual sin fricción para los usuarios."].map((t, i) => (
            <li key={i} className="relative pl-4">
              <span className="absolute left-0 top-2 h-8 w-[3px] rounded-full bg-gradient-to-b from-green-500 to-emerald-400" />
              <span className="inline-flex items-start gap-2"><CheckCircle2 className="mt-0.5 h-5 w-5 text-green-600" /> {t}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Preguntas frecuentes (corto) */}
      <div className="mt-10 grid gap-6 md:grid-cols-2">
        <div className="glass-card p-6">
          <div className="font-semibold text-slate-900">¿Necesito capacitación?</div>
          <p className="mt-2 text-slate-700 text-sm">No. La interfaz es directa: abre el mapa, busca un buque o marca tus favoritos. En minutos estás operando.</p>
        </div>
        <div className="glass-card p-6">
          <div className="font-semibold text-slate-900">¿Qué alertas soporta?</div>
          <p className="mt-2 text-slate-700 text-sm">Entrada/salida de geocercas y notificaciones por puertos. Agregaremos más tipos según prioridad de los usuarios.</p>
        </div>
      </div>

      {/* CTA */}
      <div className="mt-10 rounded-2xl p-1 bg-gradient-to-r from-red-500 to-rose-400 section-surface">
        <div className="glass-card flex items-center justify-between gap-4 p-6">
          <div>
            <div className="text-slate-900 font-semibold">¿Listo para probarlo?</div>
            <p className="text-slate-700 text-sm">Solicita acceso beta o explora el mapa si ya tienes credenciales.</p>
          </div>
          <a href="/map" className="inline-flex items-center rounded-xl bg-red-600 px-5 py-3 text-white text-sm font-medium hover:bg-red-700">
            Ir al mapa <ArrowRight className="ml-2 h-4 w-4" />
          </a>
        </div>
      </div>
    </section>
  );
}
