const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(`${BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(init?.headers || {}),
    },
    ...init,
  });
  if (!resp.ok) {
    let detail = "Request failed";
    try { detail = (await resp.json())?.detail ?? detail; } catch {}
    throw new Error(detail);
  }
  try {
    return await resp.json();
  } catch {
    // allow 204/empty json
    return undefined as unknown as T;
  }
}
