"use client";
import { Suspense } from "react";
import { Protected } from "@/components/auth/Protected";
import AisLiveMap from "@/app/(app)/map/components/ais/AisLiveMap";

export default function MapPage() {
  return (
    <>
      <Suspense fallback={
        <div className="fixed inset-0 z-0">
          <div className="w-full h-full bg-slate-100/30" />
          <div className="absolute top-3 right-3 z-50">
            <div className="px-3 py-1 rounded-full text-xs font-medium flex items-center gap-2" style={{background: 'rgba(255,255,255,0.9)'}}>
              <span className={`w-2 h-2 rounded-full bg-rose-500`} />
              <span>Desconectado</span>
              <span className="text-slate-600">·</span>
              <span className="text-slate-600">0 buques</span>
            </div>
          </div>
        </div>
      }>
        <Protected>
          <AisLiveMap token={process.env.NEXT_PUBLIC_AISSTREAM_KEY ?? ""} />
        </Protected>
      </Suspense>
    </>
  );
}
