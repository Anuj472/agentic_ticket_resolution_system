import axios, { AxiosInstance } from "axios";

const API_BASE = "/api/proxy";

/**
 * Centralized API client with automatic auth token management.
 *
 * - Caches JWT in sessionStorage to avoid re-login on every render
 * - Auto-retries once on 401 with a fresh token
 * - Single source of truth for auth logic (no more copy-paste)
 */

async function getToken(): Promise<string> {
  const cached = sessionStorage.getItem("auth_token");
  if (cached) return cached;

  const r = await axios.post(`${API_BASE}/auth/login`, {
    email: "admin@company.com",
    password: "Admin@1234",
  });

  const token: string = r.data.access_token;
  sessionStorage.setItem("auth_token", token);
  return token;
}

export function clearToken(): void {
  sessionStorage.removeItem("auth_token");
}

/**
 * Make an authenticated API call with auto-retry on 401.
 */
export async function apiCall<T = any>(
  method: "GET" | "POST" | "PATCH" | "DELETE",
  path: string,
  data?: any
): Promise<T> {
  const token = await getToken();
  try {
    const r = await axios({
      method,
      url: `${API_BASE}${path}`,
      data,
      headers: { Authorization: `Bearer ${token}` },
    });
    return r.data;
  } catch (e: any) {
    if (e?.response?.status === 401) {
      clearToken();
      const freshToken = await getToken();
      const r = await axios({
        method,
        url: `${API_BASE}${path}`,
        data,
        headers: { Authorization: `Bearer ${freshToken}` },
      });
      return r.data;
    }
    throw e;
  }
}

/**
 * Convenience wrappers
 */
export const api = {
  get: <T = any>(path: string) => apiCall<T>("GET", path),
  post: <T = any>(path: string, data?: any) => apiCall<T>("POST", path, data),
  patch: <T = any>(path: string, data?: any) => apiCall<T>("PATCH", path, data),
  delete: <T = any>(path: string) => apiCall<T>("DELETE", path),
};
