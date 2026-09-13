const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL?.replace(/\/$/, "");
const SUPABASE_ANON_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

type AuthResponse = {
  access_token?: string;
  refresh_token?: string;
  expires_in?: number;
  expires_at?: number;
  msg?: string;
  error_description?: string;
};

export type AuthSessionResponse = {
  access_token: string;
  refresh_token: string;
  expires_in?: number;
  expires_at?: number;
};

export class AuthRequestError extends Error {
  constructor(message: string, readonly status: number) { super(message); }
}

async function authRequest(path: string, body: object, signal?: AbortSignal): Promise<AuthResponse> {
  if (!SUPABASE_URL || !SUPABASE_ANON_KEY) {
    throw new Error("Supabase frontend environment is not configured.");
  }
  const response = await fetch(`${SUPABASE_URL}${path}`, {
    method: "POST",
    headers: {
      apikey: SUPABASE_ANON_KEY,
      Authorization: `Bearer ${SUPABASE_ANON_KEY}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify(body),
    signal,
  });
  const payload = (await response.json()) as AuthResponse;
  if (!response.ok) {
    throw new AuthRequestError(payload.msg ?? payload.error_description ?? "Authentication failed.", response.status);
  }
  return payload;
}

function sessionResponse(payload: AuthResponse): AuthSessionResponse {
  if (!payload.access_token || !payload.refresh_token) throw new Error("No authentication session was returned.");
  return { access_token: payload.access_token, refresh_token: payload.refresh_token,
    expires_at: payload.expires_at, expires_in: payload.expires_in };
}

export async function signInSession(email: string, password: string): Promise<AuthSessionResponse> {
  return sessionResponse(await authRequest("/auth/v1/token?grant_type=password", { email, password }));
}

export async function signUpSession(email: string, password: string): Promise<AuthSessionResponse | null> {
  const payload = await authRequest("/auth/v1/signup", { email, password });
  return payload.access_token ? sessionResponse(payload) : null;
}

export async function refreshAuthSession(refreshToken: string): Promise<AuthSessionResponse> {
  return sessionResponse(await authRequest("/auth/v1/token?grant_type=refresh_token",
    { refresh_token: refreshToken }, AbortSignal.timeout(20000)));
}

export async function signIn(email: string, password: string): Promise<string> {
  const payload = await authRequest("/auth/v1/token?grant_type=password", { email, password });
  if (!payload.access_token) throw new Error("No access token was returned.");
  return payload.access_token;
}

export async function signUp(email: string, password: string): Promise<string | null> {
  const payload = await authRequest("/auth/v1/signup", { email, password });
  return payload.access_token ?? null;
}
