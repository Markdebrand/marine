"use client";
// Por defecto usamos el proxy /api del Nginx del frontend
const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "/api";

function baseUrlJoin(path: string): string {
  const base = BASE_URL.endsWith("/") ? BASE_URL.slice(0, -1) : BASE_URL;
  return `${base}${path.startsWith("/") ? path : `/${path}`}`;
}

// Acceso al estado de auth sin hooks (Zustand)
import { useAuthStore } from "@/store/authStore";
type AuthStoreShape = {
  accessToken?: string | null;
  refreshToken: string | null;
  setRefreshToken: (t: string | null) => void;
  setLoginAt: (ts: number) => void;
  setAccessToken?: (t: string | null) => void;
};
function getAuthState(): AuthStoreShape {
  return useAuthStore.getState() as AuthStoreShape;
}

async function tryRefreshOnce(): Promise<boolean> {
  const state = getAuthState();
  const rt: string | null = state.refreshToken || null;
  if (!rt) return false;
  try {
    const resp = await fetch(baseUrlJoin("/auth/refresh"), {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: rt }),
      keepalive: true,
    });
    if (!resp.ok) return false;
    const data: { access_token: string; refresh_token?: string } = await resp.json();
    if (data?.refresh_token) state.setRefreshToken(data.refresh_token);
    state.setLoginAt(Date.now());
    // Si hay access_token y no usamos cookies, también actualizar en memoria
    state.setAccessToken?.(data?.access_token || null);
    // access_token llega como cookie HttpOnly; no necesitamos guardarlo
    return true;
  } catch {
    return false;
  }
}

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const url = baseUrlJoin(path);
  const doFetch = async (): Promise<Response> => {
    const st = getAuthState();
    const bearer: string | null = st?.accessToken || null;
    try {
      // Debug: log auth-related outgoing requests
      if (path.startsWith('/auth')) {
  console.debug('[apiFetch] outgoing', { path, hasBearer: !!bearer, init });
      }
    } catch {}
    return fetch(url, {
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
        ...(bearer ? { Authorization: `Bearer ${bearer}` } : {}),
        ...(init?.headers || {}),
      },
      ...init,
    });
  };

  let resp = await doFetch();
  if (resp.status === 401 && !url.endsWith("/auth/login") && !url.endsWith("/auth/refresh")) {
    const refreshed = await tryRefreshOnce();
    if (refreshed) {
      resp = await doFetch();
    }
  }

  if (!resp.ok) {
    let detail = "Request failed";
    try {
      const body = await resp.json();
      try {
        if (path.startsWith('/auth')) {
          // Debug: log auth-related responses
          console.debug('[apiFetch] response', { path, status: resp.status, body });
        }
      } catch {}
      detail = body?.detail ?? detail;
      // Mensaje más claro para 409 de sesión activa
      if (resp.status === 409 && typeof body?.detail === "object" && body?.detail?.code === "single_session_active") {
        detail = body.detail.message || "Otra sesión activa. Cierra la otra sesión para continuar.";
      }
    } catch {}
    const err = new Error(detail);
    // @ts-expect-error agregar meta útil
    err.status = resp.status;
    throw err;
  }
  try {
    return (await resp.json()) as T;
  } catch {
    // permitir 204/empty
    return undefined as unknown as T;
  }
}
