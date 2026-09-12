export const ACCESS_TOKEN_STORAGE_KEY = "fluentloop_access_token";
export const ACCESS_TOKEN_STORAGE_EVENT = "fluentloop-access-token-change";

export function storeAccessToken(accessToken: string): void {
  sessionStorage.setItem(ACCESS_TOKEN_STORAGE_KEY, accessToken);
  window.dispatchEvent(new Event(ACCESS_TOKEN_STORAGE_EVENT));
}

export function clearAccessToken(): void {
  sessionStorage.removeItem(ACCESS_TOKEN_STORAGE_KEY);
  window.dispatchEvent(new Event(ACCESS_TOKEN_STORAGE_EVENT));
}

export function getStoredAccessToken(): string {
  if (typeof window === "undefined") return "";
  return sessionStorage.getItem(ACCESS_TOKEN_STORAGE_KEY) ?? "";
}
