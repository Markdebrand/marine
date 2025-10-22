// Por defecto usamos el proxy /api del Nginx del frontend
const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "/api";

export async function apiFetch<T>(
  path: string,
  init?: RequestInit
): Promise<T> {
  const base = BASE_URL.endsWith("/") ? BASE_URL.slice(0, -1) : BASE_URL;
  const resp = await fetch(`${base}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
    ...init,
  });
  if (!resp.ok) {
    let detail = "Request failed";
    try {
      detail = (await resp.json())?.detail ?? detail;
    } catch {}
    throw new Error(detail);
  }
  try {
    return await resp.json();
  } catch {
    // allow 204/empty json
    return undefined as unknown as T;
  }
}
