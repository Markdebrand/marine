"use client";
import AppHeader from "@/app/(app)/components/AppHeader";
import PersistentMapHost from "@/app/(app)/components/PersistentMapHost";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-white">
      <AppHeader />
      {/* Mapa persistente (se monta una vez y se oculta/ muestra según la ruta) */}
      <PersistentMapHost />
      <div className="mx-auto max-w-7xl px-6 py-6">{children}</div>
    </div>
  );
}
