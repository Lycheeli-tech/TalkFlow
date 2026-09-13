import { AuthRequestError, refreshAuthSession, type AuthSessionResponse } from "./auth";

export const ACCESS_TOKEN_STORAGE_KEY = "fluentloop_access_token";
export const ACCESS_TOKEN_STORAGE_EVENT = "fluentloop-access-token-change";
export const AUTH_SESSION_STORAGE_KEY = "fluentloop_auth_session";

type StoredSession = AuthSessionResponse & { expires_at: number };
let refreshing: Promise<string> | null = null;

function storedSession(): StoredSession | null {
  if (typeof window === "undefined") return null;
  try {
    const value = JSON.parse(localStorage.getItem(AUTH_SESSION_STORAGE_KEY) ?? "null");
    return value && typeof value.access_token === "string" && typeof value.refresh_token === "string"
      && typeof value.expires_at === "number" ? value : null;
  } catch { return null; }
}

export function storeAuthSession(session: AuthSessionResponse): void {
  localStorage.setItem(AUTH_SESSION_STORAGE_KEY, JSON.stringify({ ...session,
    expires_at: session.expires_at ?? Math.floor(Date.now() / 1000) + (session.expires_in ?? 3600) }));
  sessionStorage.setItem(ACCESS_TOKEN_STORAGE_KEY, session.access_token);
  window.dispatchEvent(new Event(ACCESS_TOKEN_STORAGE_EVENT));
}

export function storeAccessToken(accessToken: string): void {
  if (storedSession()?.access_token !== accessToken) localStorage.removeItem(AUTH_SESSION_STORAGE_KEY);
  sessionStorage.setItem(ACCESS_TOKEN_STORAGE_KEY, accessToken);
  window.dispatchEvent(new Event(ACCESS_TOKEN_STORAGE_EVENT));
}

export function clearAccessToken(): void {
  localStorage.removeItem(AUTH_SESSION_STORAGE_KEY);
  sessionStorage.removeItem(ACCESS_TOKEN_STORAGE_KEY);
  window.dispatchEvent(new Event(ACCESS_TOKEN_STORAGE_EVENT));
}

export function getStoredAccessToken(): string {
  if (typeof window === "undefined") return "";
  return storedSession()?.access_token ?? sessionStorage.getItem(ACCESS_TOKEN_STORAGE_KEY) ?? "";
}

export async function getValidAccessToken(forceRefresh = false): Promise<string> {
  const session = storedSession();
  if (!session || (!forceRefresh && session.expires_at > Date.now() / 1000 + 60)) return getStoredAccessToken();
  if (refreshing) return refreshing;
  refreshing = (async () => {
    try {
      const next = await refreshAuthSession(session.refresh_token);
      // A logout/new login/another tab's refresh must not be overwritten by a late response.
      if (storedSession()?.refresh_token !== session.refresh_token) return getStoredAccessToken();
      storeAuthSession(next);
      return next.access_token;
    } catch (error) {
      if (storedSession()?.refresh_token !== session.refresh_token) return getStoredAccessToken();
      if (error instanceof AuthRequestError && (error.status === 400 || error.status === 401)) clearAccessToken();
      throw error; // Network/provider failures retain the session for retry.
    } finally { refreshing = null; }
  })();
  return refreshing;
}

export async function sessionFetch(url: string, init?: RequestInit): Promise<Response> {
  const requestedOwner = tokenOwner(getStoredAccessToken());
  async function send(token: string) {
    const headers = new Headers(init?.headers);
    headers.set("Authorization", `Bearer ${token}`);
    return fetch(url, { ...init, headers });
  }
  let token = await getValidAccessToken();
  const owner = tokenOwner(token);
  if (requestedOwner && requestedOwner !== owner) throw new Error("Account changed. Please retry the request.");
  let result = await send(token);
  if (result.status === 401 && storedSession() && getStoredAccessToken() === token) {
    const renewed = await getValidAccessToken(true);
    if (renewed && owner && tokenOwner(renewed) === owner) {
      token = renewed;
      result = await send(token); // Auth rejected the first request before product writes.
    }
  }
  if (result.status === 401 && getStoredAccessToken() === token) clearAccessToken();
  return result;
}

function tokenOwner(token: string): string | null {
  try { return JSON.parse(atob(token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/"))).sub ?? null; }
  catch { return null; }
}

export function maintainAuthSession(): () => void {
  const check = () => { if (storedSession()) void getValidAccessToken().catch(() => {}); };
  check();
  const timer = window.setInterval(check, 30000);
  const visible = () => { if (document.visibilityState === "visible") check(); };
  const synchronized = (event: StorageEvent) => {
    if (event.key !== AUTH_SESSION_STORAGE_KEY) return;
    const session = storedSession();
    if (session) sessionStorage.setItem(ACCESS_TOKEN_STORAGE_KEY, session.access_token);
    else sessionStorage.removeItem(ACCESS_TOKEN_STORAGE_KEY);
    window.dispatchEvent(new Event(ACCESS_TOKEN_STORAGE_EVENT));
  };
  window.addEventListener("focus", check);
  window.addEventListener("storage", synchronized);
  document.addEventListener("visibilitychange", visible);
  return () => { window.clearInterval(timer); window.removeEventListener("focus", check);
    window.removeEventListener("storage", synchronized);
    document.removeEventListener("visibilitychange", visible); };
}
