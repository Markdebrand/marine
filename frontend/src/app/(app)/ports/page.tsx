"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Search, MapPin, Navigation, Anchor } from "lucide-react";
import { apiFetch } from "@/lib/api";

export default function PortSearchPage() {
  const router = useRouter();
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [errorPrompt, setErrorPrompt] = useState("");

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    const val = query.trim();
    if (!val) return;

    setLoading(true);
    setErrorPrompt("");

    try {
      // Usamos el endpoint existente que busca por UN/LOCODE o hace fallback a búsqueda por nombre
      // El backend devuelve { port_number, port_name, unlocode, ... }
      const port = await apiFetch<any>(`/ports/search?unlocode=${encodeURIComponent(val)}`);
      
      if (port && port.unlocode) {
        // Redirigir al URL canónico usando el UN/LOCODE sin espacios
        router.push(`/ports/${port.unlocode.replace(/\s+/g, "")}`);
      } else if (port && port.port_number) {
        // Fallback por si acaso algún puerto no tiene unlocode
        router.push(`/ports/${port.port_number}`);
      }
    } catch (err: any) {
      setErrorPrompt(
        err.message?.includes("not found") 
          ? "No port found matching that name or UN/LOCODE."
          : "An error occurred while searching."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <main className="py-10 px-4 md:px-0 max-w-4xl mx-auto flex flex-col items-center justify-center min-h-[70vh] animate-in fade-in slide-in-from-bottom-4 duration-500">
        
        {/* Encabezado Principal */}
        <div className="text-center mb-10 w-full">
          <div className="mx-auto flex h-20 w-20 items-center justify-center rounded-full bg-gradient-to-br from-indigo-500 to-indigo-700 text-white shadow-xl shadow-indigo-500/30 mb-6">
            <Anchor className="h-10 w-10" />
          </div>
          <h1 className="text-4xl md:text-5xl font-extrabold text-slate-900 tracking-tight">
            Global Port <span className="text-indigo-600">Search</span>
          </h1>
          <p className="mt-4 text-lg text-slate-600 max-w-2xl mx-auto">
            Instantly locate thousands of marine ports worldwide. Search by formal <span className="font-semibold text-slate-700">UN/LOCODE</span> (e.g. US MIA) or simply enter the <span className="font-semibold text-slate-700">Port Name</span> (e.g. Miami).
          </p>
        </div>

        {/* Buscador Card */}
        <div className="w-full max-w-2xl glass-card p-6 md:p-8 bg-white/80 backdrop-blur-md rounded-3xl shadow-[0_8px_30px_rgb(0,0,0,0.06)] border border-slate-200 relative overflow-hidden">
          <div className="absolute -right-20 -bottom-20 h-64 w-64 rounded-full bg-[rgba(99,102,241,0.08)] blur-[60px] pointer-events-none" />
          
          <form onSubmit={handleSearch} className="relative z-10 flex flex-col sm:flex-row gap-4">
            <div className="relative flex-grow">
              <div className="absolute inset-y-0 left-0 flex items-center pl-4 pointer-events-none">
                <Search className="h-6 w-6 text-slate-400" />
              </div>
              <input
                type="text"
                className="w-full pl-12 pr-4 py-4 bg-slate-50 border border-slate-200 rounded-2xl text-lg text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-4 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all font-medium"
                placeholder="Ex. 'Crescent City' or 'USCEC'"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                disabled={loading}
                autoFocus
              />
            </div>
            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="py-4 px-8 bg-indigo-600 hover:bg-indigo-700 disabled:opacity-70 disabled:hover:bg-indigo-600 outline-none focus:ring-4 focus:ring-indigo-500/20 text-white rounded-2xl font-bold text-lg transition-all flex items-center justify-center gap-2"
            >
              {loading ? (
                <>
                  <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                  Searching...
                </>
              ) : (
                "Search"
              )}
            </button>
          </form>

          {errorPrompt && (
            <div className="mt-6 p-4 bg-rose-50 border border-rose-100 rounded-xl text-rose-600 flex items-start gap-3 animate-in fade-in">
              <span className="text-xl">⚠️</span>
              <div>
                <p className="font-semibold">Match Not Found</p>
                <p className="text-sm mt-0.5 text-rose-500">{errorPrompt}</p>
              </div>
            </div>
          )}

          <div className="mt-8 grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div className="bg-slate-50/50 border border-slate-100 rounded-2xl p-4 flex gap-3">
              <MapPin className="text-indigo-400 h-5 w-5 shrink-0" />
              <div>
                <h4 className="text-sm font-bold text-slate-700">Search by Name</h4>
                <p className="text-xs text-slate-500 leading-tight mt-1">Smart fallback matches partial harbor names globally.</p>
              </div>
            </div>
            <div className="bg-slate-50/50 border border-slate-100 rounded-2xl p-4 flex gap-3">
              <Navigation className="text-emerald-400 h-5 w-5 shrink-0" />
              <div>
                <h4 className="text-sm font-bold text-slate-700">Search by UN/LOCODE</h4>
                <p className="text-xs text-slate-500 leading-tight mt-1">Precise 5-character identification standardized worldwide.</p>
              </div>
            </div>
          </div>
        </div>

      </main>
    </>
  );
}
