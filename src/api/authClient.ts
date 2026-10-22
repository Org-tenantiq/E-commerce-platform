export class AuthExpiredError extends Error {
  constructor() {
    super("Session expired");
    this.name = "AuthExpiredError";
  }
}

// Held in module memory only; never written to web storage.
let accessToken: string | null = null;

async function postToken(path: string, body?: unknown): Promise<boolean> {
  const res = await fetch(path, {
    method: "POST",
    credentials: "include",
    headers: body === undefined ? {} : { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!res.ok) return false;
  const data = (await res.json()) as { access_token?: string };
  accessToken = data.access_token ?? null;
  return accessToken !== null;
}

function send(input: string, init: RequestInit): Promise<Response> {
  const headers: Record<string, string> = {
    ...(init.headers as Record<string, string> | undefined),
  };
  if (accessToken) headers.Authorization = `Bearer ${accessToken}`;
  return fetch(input, { ...init, headers });
}

export const authClient = {
  async login(email: string, password: string): Promise<void> {
    const res = await fetch("/api/auth/login", {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) {
      throw { status: res.status };
    }
    const data = (await res.json()) as { access_token?: string };
    accessToken = data.access_token ?? null;
  },

  async register(email: string, password: string): Promise<void> {
    const res = await fetch("/api/auth/register", {
      method: "POST",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    if (!res.ok) {
      throw { status: res.status };
    }
    const data = (await res.json()) as { access_token?: string };
    accessToken = data.access_token ?? null;
  },

  async request(input: string, init: RequestInit = {}): Promise<Response> {
    const res = await send(input, init);
    if (res.status !== 401) return res;
    if (!(await postToken("/api/auth/refresh").catch(() => false))) {
      accessToken = null;
      throw new AuthExpiredError();
    }
    return send(input, init);
  },

  getToken(): string | null {
    return accessToken;
  },

  clear(): void {
    accessToken = null;
  },
};
