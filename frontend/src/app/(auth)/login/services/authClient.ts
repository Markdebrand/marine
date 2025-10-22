import type { AuthCredentials } from "../types/auth";
import { authService } from "@/services/authService";

// Login contra el backend; deja cookies y refresh_token en memoria
export async function login(credentials: AuthCredentials) {
  return authService.login({ email: credentials.email, password: credentials.password });
}
