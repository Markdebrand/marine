import { apiFetch } from "@/lib/api";
import { useAuthStore, type AuthUser } from "@/store/authStore";

export type LoginInput = { email: string; password: string };
export type TokenResponse = {
  access_token: string;
  token_type: string;
  refresh_token?: string;
};

export type ProfileResponse = {
  id: number;
  email: string;
  role: string;
  is_superadmin?: boolean | null;
  first_name?: string | null;
  last_name?: string | null;
  phone?: string | null;
  company?: string | null;
  website?: string | null;
  bio?: string | null;
  plan_code?: string | null;
  plan_name?: string | null;
  subscription_id?: number | null;
  subscription_status?: string | null;
};

export const authService = {
  async login(body: LoginInput) {
    const res = await apiFetch<TokenResponse>(`/auth/login`, {
      method: "POST",
      body: JSON.stringify(body),
    });
    const { setRefreshToken, setAccessToken, setLoginAt } = useAuthStore.getState();
    if (res?.refresh_token) setRefreshToken(res.refresh_token);
    if (res?.access_token) setAccessToken(res.access_token);
    setLoginAt(Date.now());
    return res;
  },
  async me(): Promise<AuthUser> {
    const p = await apiFetch<ProfileResponse>(`/auth/me`);
    return {
      id: p.id,
      email: p.email,
      role: p.role,
      is_superadmin: p.is_superadmin,
      subscription_status: p.subscription_status,
      plan_code: p.plan_code,
      first_name: p.first_name,
      last_name: p.last_name,
    };
  },
  async logout() {
    const state = useAuthStore.getState();
    const rt = state.refreshToken;
    const active_seconds = state.loginAt ? Math.max(1, Math.floor((Date.now() - state.loginAt) / 1000)) : undefined;
    try {
      const payload = { refresh_token: rt ?? undefined, active_seconds };
      console.debug('[authService.logout] sending', { payload: rt ? '[redacted]' : null, active_seconds });
      const res = await apiFetch(`/auth/logout`, {
        method: "POST",
        body: JSON.stringify(payload),
        // Mantener la conexión viva si se llama desde unload (navegador)
        keepalive: true,
      });
      console.debug('[authService.logout] response', res);
    } catch {
      // best-effort
    }
    // Limpia estado local
    useAuthStore.getState().resetAuth();
  },
  async ping() {
    const state = useAuthStore.getState();
    const rt = state.refreshToken;
    try {
      await apiFetch(`/auth/ping`, {
        method: "POST",
        body: JSON.stringify({ refresh_token: rt ?? undefined }),
      });
    } catch {}
  },
};
