"use client";
import AppHeader from "@/app/(app)/components/AppHeader";
import PersistentMapHost from "@/app/(app)/components/PersistentMapHost";
import { useSubscriptionGuard } from "@/hooks/useSubscriptionGuard";

export default function AppLayout({ children }: { children: React.ReactNode }) {
  // Verificar estado de suscripción y redirigir a /profile si no está activa
  useSubscriptionGuard();

  return (
    <div className="min-h-screen bg-white">
      <AppHeader />
      {/* Mapa persistente (se monta una vez y se oculta/ muestra según la ruta) */}
      <PersistentMapHost />
      <div className="mx-auto max-w-7xl px-6 py-6">{children}</div>
    </div>
  );
}
