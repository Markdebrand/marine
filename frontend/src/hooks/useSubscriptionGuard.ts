"use client";
import { useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useAuthStore } from "@/store/authStore";

/**
 * Hook que verifica el estado de suscripción del usuario y redirige a /profile
 * si la suscripción no está activa.
 * 
 * Excepciones:
 * - Administradores (is_superadmin o role === 'admin')
 * - Usuarios ya en la página /profile
 */
export function useSubscriptionGuard() {
  const router = useRouter();
  const pathname = usePathname();
  const { user, status } = useAuthStore();

  useEffect(() => {
    // Solo verificar si el usuario está autenticado
    if (status !== "authenticated" || !user) return;

    // Excluir admins
    const isAdmin = user.is_superadmin || user.role === "admin";
    if (isAdmin) return;

    // No redirigir si ya estamos en /profile
    if (pathname === "/profile") return;

    // Verificar estado de suscripción
    const subscriptionStatus = user.subscription_status;
    
    // Si no tiene suscripción activa, redirigir a /profile
    if (subscriptionStatus !== "active") {
      console.log("[useSubscriptionGuard] Subscription not active, redirecting to /profile");
      router.push("/profile");
    }
  }, [user, status, pathname, router]);
}
