const BASE_URL = process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:8000";

let authToken: string | null = null;

export function setAuthToken(token: string | null) {
  authToken = token;
}

export class ApiError extends Error {
  constructor(public status: number, detail: string) {
    super(detail);
    this.name = "ApiError";
  }
}

export async function api<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init.headers as Record<string, string>),
  };
  if (authToken) headers.Authorization = `Bearer ${authToken}`;

  const resp = await fetch(`${BASE_URL}${path}`, { ...init, headers });

  if (!resp.ok) {
    let detail = `HTTP ${resp.status}`;
    try {
      const body = await resp.json();
      if (body?.detail) {
        detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
      }
    } catch {
      // corpo não-JSON — mantém o detail genérico
    }
    throw new ApiError(resp.status, detail);
  }
  if (resp.status === 204) return undefined as T;
  return resp.json();
}
