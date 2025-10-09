"use client";
import { ReactNode, useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/useAuth";
import { authService } from "@/services/authService";

export function Protected({ children }: { children: ReactNode }) {
  const { token } = useAuth();
  const router = useRouter();

  useEffect(() => {
    let cancelled = false;
    const ensure = async () => {
      if (!token) {
        router.replace("/login");
        return;
      }
      try {
        await authService.me(token);
      } catch {
        if (cancelled) return;
        // token inválido/expirado
        router.replace("/login");
      }
    };
    ensure();
    return () => { cancelled = true; };
  }, [token, router]);

  if (!token) return null;
  return <>{children}</>;
}
