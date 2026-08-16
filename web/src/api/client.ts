import { ApiError } from "./types";
import { useAuthStore } from "../store/authStore";

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api/v1";

let refreshPromise: Promise<string | null> | null = null;

async function doRefresh(): Promise<string | null> {
  const refreshToken = useAuthStore.getState().refreshToken;
  if (!refreshToken) return null;
  try {
    const res = await fetch(`${API_BASE_URL}/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
    if (!res.ok) {
      useAuthStore.getState().clearAuth();
      return null;
    }
    const data = await res.json();
    useAuthStore.getState().setTokens(data.access_token, data.refresh_token);
    return data.access_token as string;
  } catch {
    return null;
  }
}

interface RequestOptions {
  method?: string;
  body?: unknown;
  auth?: boolean;
  form?: boolean;
}

async function request<T>(path: string, options: RequestOptions = {}, isRetry = false): Promise<T> {
  const { method = "GET", body, auth = false, form = false } = options;
  const headers: Record<string, string> = {};
  if (!form && body !== undefined) headers["Content-Type"] = "application/json";

  if (auth) {
    const token = useAuthStore.getState().accessToken;
    if (token) headers["Authorization"] = `Bearer ${token}`;
  }

  const res = await fetch(`${API_BASE_URL}${path}`, {
    method,
    headers,
    body: body === undefined ? undefined : form ? (body as BodyInit) : JSON.stringify(body),
  });

  if (res.status === 401 && auth && !isRetry) {
    if (!refreshPromise) refreshPromise = doRefresh().finally(() => (refreshPromise = null));
    const newToken = await refreshPromise;
    if (newToken) return request<T>(path, options, true);
  }

  if (!res.ok) {
    let message = res.statusText;
    try {
      const data = await res.json();
      message = typeof data.detail === "string" ? data.detail : JSON.stringify(data.detail ?? data);
    } catch {
      /* body wasn't JSON */
    }
    throw new ApiError(res.status, message);
  }

  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const api = {
  get: <T>(path: string, auth = false) => request<T>(path, { method: "GET", auth }),
  post: <T>(path: string, body?: unknown, auth = false) => request<T>(path, { method: "POST", body, auth }),
  patch: <T>(path: string, body?: unknown, auth = false) => request<T>(path, { method: "PATCH", body, auth }),
  delete: <T>(path: string, auth = false) => request<T>(path, { method: "DELETE", auth }),
  postForm: <T>(path: string, body: URLSearchParams) => request<T>(path, { method: "POST", body: body as unknown as BodyInit, form: true }),
};

export function formatPrice(cents: number): string {
  return (cents / 100).toLocaleString("en-US", { style: "currency", currency: "USD" });
}
