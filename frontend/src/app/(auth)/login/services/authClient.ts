import type { AuthCredentials, AuthResponse } from "../types/auth";
import { apiFetch } from "@/lib/api";

// Real login against backend
export async function login(
  credentials: AuthCredentials
): Promise<AuthResponse> {
  const res = await apiFetch<{ access_token: string; refresh_token?: string }>(
    `/auth/login`,
    {
      method: "POST",
      body: JSON.stringify({
        email: credentials.email,
        password: credentials.password,
      }),
    }
  );
  return { token: res.access_token, user: { email: credentials.email } };
}
