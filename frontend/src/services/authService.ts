import { apiFetch } from "@/lib/api";

export type LoginInput = { email: string; password: string };
export type TokenResponse = { access_token: string; token_type: string; refresh_token?: string };

export const authService = {
  async login(body: LoginInput) {
    return apiFetch<TokenResponse>(`/auth/login`, {
      method: "POST",
      body: JSON.stringify(body),
    });
  },
  async me(token: string) {
    return apiFetch<{ id: string; email: string }>(`/whoami`, {
      headers: { Authorization: `Bearer ${token}` },
    });
  },
};
