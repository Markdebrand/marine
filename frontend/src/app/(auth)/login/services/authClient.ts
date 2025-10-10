import type { AuthCredentials, AuthResponse } from "../types/auth";

export async function login(credentials: AuthCredentials): Promise<AuthResponse> {
  const { email, password } = credentials;
  await new Promise((r) => setTimeout(r, 400));
  const isValid = email === "admin@example.com" && password === "admin123";
  if (!isValid) throw new Error("Invalid credentials");
  return { token: "static-dev-token", user: { email } };
}
