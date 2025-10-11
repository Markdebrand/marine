import { Suspense } from "react";
import { Protected } from "@/components/auth/Protected";
import OpenLayersMap from "@/components/OpenLayersMap";

export default function MapPage() {
  return (
    <main className="min-h-[100vh] py-6">
        <section className="section-surface">
        <Suspense
          fallback={
            <div className="w-full rounded-lg overflow-hidden border border-slate-200" style={{ height: 640 }} />
          }
        >
          <Protected>
            <OpenLayersMap height={640} seamarkZoomOffset={3} />
          </Protected>
        </Suspense>
      </section>
    </main>
  );
}
