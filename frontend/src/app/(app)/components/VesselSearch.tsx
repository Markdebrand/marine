"use client";

import { useState } from "react";
import { Search } from "lucide-react";
import { useMapStore } from "@/app/(app)/map/store/mapStore";
import { useRouter } from "next/navigation";

interface VesselData {
  ship_name: string;
  ship_type: string;
  flag: string;
  call_sign: string;
  latitude?: number;
  longitude?: number;
}

interface VesselDetailsWrapper {
  mmsi: string;
  data: VesselData;
  status: string;
}

export default function VesselSearch() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<VesselDetailsWrapper | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  const setView = useMapStore((s) => s.setView);
  const router = useRouter();

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      // URL directa a /details ya que en main.py no hay prefijo global /api
      // Usamos variable de entorno si existe, o localhost:8000 por defecto
      const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${baseUrl}/details/${encodeURIComponent(query.trim())}`);
      
      if (!res.ok) {
        throw new Error("Vessel not found or error fetching details");
      }
      const data: VesselDetailsWrapper = await res.json();
      setResult(data);

      // If coordinates are available, center map
      if (data.data.latitude && data.data.longitude) {
        // Switch to map page if not already there
        router.push("/map");
        
        // Short delay to allow map to mount if it wasn't
        setTimeout(() => {
             if (data.data.latitude && data.data.longitude) {
                // MapLibre expects [lng, lat]
                setView([data.data.longitude, data.data.latitude], 12);
             }
        }, 100);
      }
    } catch (err: any) {
      setError(err.message || "Error searching vessel");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative">
      <form onSubmit={handleSearch} className="flex items-center">
        <div className="relative">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search MMSI or Name..."
            className="pl-9 pr-4 py-1 rounded-full border border-slate-300 bg-white/50 backdrop-blur-sm text-sm focus:outline-none focus:ring-2 focus:ring-red-500 w-48 shadow-sm transition-all focus:w-64"
          />
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-slate-500" />
        </div>
      </form>

      {/* Result Popover */}
      {(result || error) && (
        <div className="absolute top-full mt-2 w-72 right-0 bg-white rounded-lg shadow-xl border border-slate-100 p-4 z-50 animate-in fade-in slide-in-from-top-2">
          {error && <p className="text-red-500 text-sm">{error}</p>}
          
          {result && (
            <div className="space-y-2">
              <h3 className="font-bold text-slate-900">{result.data.ship_name}</h3>
              <div className="text-xs text-slate-600 space-y-1">
                <p>MMSI: <span className="font-mono text-slate-800">{result.mmsi}</span></p>
                <p>Type: {result.data.ship_type}</p>
                <p>Flag: {result.data.flag || "N/A"}</p>
                <p>Call Sign: {result.data.call_sign}</p>
              </div>
              
              {result.data.latitude && result.data.longitude ? (
                <div className="mt-2 text-xs text-green-600 flex items-center gap-1">
                   <span>✓ Live Position Available</span>
                </div>
              ) : (
                 <div className="mt-2 text-xs text-amber-600">
                   ⚠ No live position
                 </div>
              )}
            </div>
          )}
          
          <button 
            onClick={() => {setResult(null); setError(null);}} 
            className="absolute top-2 right-2 text-slate-400 hover:text-slate-600"
          >
            ×
          </button>
        </div>
      )}
    </div>
  );
}
