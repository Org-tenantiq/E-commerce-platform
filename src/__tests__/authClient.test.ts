import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { AuthExpiredError, authClient } from "../api/authClient";

const json = (status: number, body: unknown = {}) =>
  new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });

describe("authClient", () => {
  let fetchMock: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    authClient.clear();
    fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
  });
  afterEach(() => {
    vi.unstubAllGlobals();
    localStorage.clear();
    sessionStorage.clear();
  });

  it("AC-1: login POSTs JSON with credentials and keeps token in memory only", async () => {
    fetchMock.mockResolvedValueOnce(json(200, { access_token: "tok1", expires_in: 900 }));
    await authClient.login("a@b.co", "pw");
    const [url, init] = fetchMock.mock.calls[0];
    expect(url).toBe("/api/auth/login");
    expect(init.method).toBe("POST");
    expect(init.credentials).toBe("include");
    expect(init.headers["Content-Type"]).toBe("application/json");
    expect(JSON.parse(init.body)).toEqual({ email: "a@b.co", password: "pw" });
    expect(authClient.getToken()).toBe("tok1");
    expect(localStorage.length).toBe(0);
    expect(sessionStorage.length).toBe(0);
  });

  it("AC-2: sends bearer token; on 401 refreshes once and retries once", async () => {
    fetchMock
      .mockResolvedValueOnce(json(200, { access_token: "old" }))
      .mockResolvedValueOnce(json(401))
      .mockResolvedValueOnce(json(200, { access_token: "new" }))
      .mockResolvedValueOnce(json(200, { ok: true }));
    await authClient.login("a@b.co", "pw");
    const res = await authClient.request("/api/things");
    expect(res.status).toBe(200);
    expect(fetchMock).toHaveBeenCalledTimes(4);
    expect(fetchMock.mock.calls[1][1].headers.Authorization).toBe("Bearer old");
    expect(fetchMock.mock.calls[2][0]).toBe("/api/auth/refresh");
    expect(fetchMock.mock.calls[2][1].method).toBe("POST");
    expect(fetchMock.mock.calls[2][1].credentials).toBe("include");
    expect(fetchMock.mock.calls[3][0]).toBe("/api/things");
    expect(fetchMock.mock.calls[3][1].headers.Authorization).toBe("Bearer new");
    expect(localStorage.length + sessionStorage.length).toBe(0);
  });

  it("AC-2: a 401 on the retry is returned without another refresh", async () => {
    fetchMock
      .mockResolvedValueOnce(json(200, { access_token: "old" }))
      .mockResolvedValueOnce(json(401))
      .mockResolvedValueOnce(json(200, { access_token: "new" }))
      .mockResolvedValueOnce(json(401));
    await authClient.login("a@b.co", "pw");
    const res = await authClient.request("/api/things");
    expect(res.status).toBe(401);
    expect(fetchMock).toHaveBeenCalledTimes(4);
  });

  it("AC-3: failed refresh clears token and throws AuthExpiredError, no retries", async () => {
    fetchMock
      .mockResolvedValueOnce(json(200, { access_token: "old" }))
      .mockResolvedValueOnce(json(401))
      .mockResolvedValueOnce(json(401));
    await authClient.login("a@b.co", "pw");
    await expect(authClient.request("/api/things")).rejects.toBeInstanceOf(AuthExpiredError);
    expect(fetchMock).toHaveBeenCalledTimes(3);
    expect(authClient.getToken()).toBeNull();
  });
});
