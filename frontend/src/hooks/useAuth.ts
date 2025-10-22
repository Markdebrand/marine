"use client";
import { useEffect } from "react";
import { useAuthStore, type AuthUser } from "@/store/authStore";
import { authService } from "@/services/authService";

export function useAuth() {
  const { status, user, refreshToken, setStatus, setUser, resetAuth } = useAuthStore();

  // Inicializar estado consultando /auth/me con cookies
  useEffect(() => {
    if (status === "idle") {
      setStatus("loading");
      authService
        .me()
        .then((u: AuthUser) => {
          setUser(u);
          setStatus("authenticated");
        })
        .catch(() => {
          resetAuth();
        });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [status]);

  // Intento de logout al cerrar la pestaña/ventana para cumplir política de cierre al cerrar navegador
  useEffect(() => {
    if (status !== "authenticated" || !refreshToken) return;
    // Mantener viva la sesión (last_seen_at) cada ~60s
    const iv = setInterval(() => {
      authService.ping();
    }, 60000);
    const onBeforeUnload = () => {
      // Best-effort: usar sendBeacon si está disponible para evitar abortos
      try {
        const payload = JSON.stringify({ refresh_token: refreshToken });
        const blob = new Blob([payload], { type: "application/json" });
        const ok = navigator.sendBeacon?.(process.env.NEXT_PUBLIC_API_URL ? `${process.env.NEXT_PUBLIC_API_URL.replace(/\/$/, "")}/auth/logout` : "/api/auth/logout", blob);
        if (!ok) {
          // fallback
          authService.logout();
        }
      } catch {
        authService.logout();
      }
    };
    window.addEventListener("beforeunload", onBeforeUnload);
    return () => {
      clearInterval(iv);
      window.removeEventListener("beforeunload", onBeforeUnload);
    };
  }, [status, refreshToken]);

  return { status, user };
}
