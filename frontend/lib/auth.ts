const SUPABASE_URL = process.env.NEXT_PUBLIC_SUPABASE_URL?.replace(/\/$/, "");
const SUPABASE_ANON_KEY = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;

type AuthResponse = {
  access_token?: string;
  msg?: string;
  error_description?: string;
};

async function authRequest(path: string, body: object): Promise<AuthResponse> {
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
  });
  const payload = (await response.json()) as AuthResponse;
  if (!response.ok) {
    throw new Error(payload.msg ?? payload.error_description ?? "Authentication failed.");
  }
  return payload;
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
