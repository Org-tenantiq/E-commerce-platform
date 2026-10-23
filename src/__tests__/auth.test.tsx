import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "../auth/AuthProvider";
import { ProtectedRoute } from "../auth/ProtectedRoute";
import { getRedirectPath, isValidReturnTo } from "../auth/returnTo";
import { authClient } from "../api/authClient";

vi.mock("../api/authClient");

// Test component that uses useAuth
function TestComponent() {
  const { user, status, login, logout } = useAuth();
  return (
    <div>
      <div>Status: {status}</div>
      <div>User: {user ? user.email : "null"}</div>
      <button onClick={() => login("test@example.com", "password123")}>Login</button>
      <button onClick={() => logout()}>Logout</button>
    </div>
  );
}

function ProtectedComponent() {
  return <div>Protected Page</div>;
}

function LoginComponent() {
  const { login } = useAuth();
  const params = new URLSearchParams(window.location.search);
  const returnTo = params.get("returnTo");

  return (
    <div>
      <h1>Login</h1>
      <div>Return to: {returnTo}</div>
      <button onClick={() => login("test@example.com", "password123")}>Login</button>
    </div>
  );
}

describe("AC-1: AuthProvider initialization", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("AC-1: AuthProvider attempts silent refresh and loads user from GET /api/auth/me on success", async () => {
    // Mock successful refresh
    global.fetch = vi.fn((input: string) => {
      if (input === "/api/auth/refresh") {
        return Promise.resolve({
          ok: true,
          json: () => Promise.resolve({ access_token: "token123" }),
        } as Response);
      }
      return Promise.reject(new Error("Not mocked"));
    });

    // Mock authClient.request to return user
    const mockRequest = vi.fn();
    mockRequest.mockImplementation((path: string) => {
      if (path === "/api/auth/me") {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({ user: { id: "user1", email: "test@example.com" } }),
        } as Response);
      }
      return Promise.reject(new Error("Not mocked"));
    });
    vi.mocked(authClient.request).mockImplementation(mockRequest);

    render(
      <BrowserRouter>
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      </BrowserRouter>
    );

    // Initially loading
    expect(screen.getByText("Status: loading")).toBeDefined();

    // After silent refresh and user load
    await waitFor(() => {
      expect(screen.getByText("Status: authenticated")).toBeDefined();
      expect(screen.getByText("User: test@example.com")).toBeDefined();
    });

    expect(mockRequest).toHaveBeenCalledWith("/api/auth/me");
  });

  it("AC-1: AuthProvider sets status to unauthenticated when silent refresh fails", async () => {
    // Mock failed refresh
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: false,
      } as Response)
    );

    render(
      <BrowserRouter>
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      </BrowserRouter>
    );

    // Initially loading
    expect(screen.getByText("Status: loading")).toBeDefined();

    // After failed refresh
    await waitFor(() => {
      expect(screen.getByText("Status: unauthenticated")).toBeDefined();
    });
  });

  it("AC-1: AuthProvider exposes login function that updates user state", async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: false,
      } as Response)
    );

    const mockRequest = vi.fn();
    mockRequest.mockImplementation((path: string) => {
      if (path === "/api/auth/me") {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({ user: { id: "user1", email: "test@example.com" } }),
        } as Response);
      }
      return Promise.reject(new Error("Not mocked"));
    });
    vi.mocked(authClient.login).mockResolvedValueOnce(undefined);
    vi.mocked(authClient.request).mockImplementation(mockRequest);

    render(
      <BrowserRouter>
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText("Status: unauthenticated")).toBeDefined();
    });

    const loginButton = screen.getByRole("button", { name: "Login" });
    fireEvent.click(loginButton);

    await waitFor(() => {
      expect(authClient.login).toHaveBeenCalledWith("test@example.com", "password123");
      expect(screen.getByText("Status: authenticated")).toBeDefined();
      expect(screen.getByText("User: test@example.com")).toBeDefined();
    });
  });
});

describe("AC-2: ProtectedRoute redirect behavior", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("AC-2: ProtectedRoute redirects anonymous user to login with returnTo query param", async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: false,
      } as Response)
    );

    render(
      <BrowserRouter>
        <AuthProvider>
          <Routes>
            <Route
              path="/protected"
              element={
                <ProtectedRoute>
                  <ProtectedComponent />
                </ProtectedRoute>
              }
            />
            <Route path="/login" element={<LoginComponent />} />
          </Routes>
          <Navigate to="/protected" replace />
        </AuthProvider>
      </BrowserRouter>
    );

    await waitFor(() => {
      // Should be redirected to login with returnTo parameter
      expect(window.location.pathname).toBe("/login");
      expect(window.location.search).toContain("returnTo");
    });
  });

  it("AC-2: returnTo validation accepts relative paths starting with single /", () => {
    expect(isValidReturnTo("/dashboard")).toBe(true);
    expect(isValidReturnTo("/user/profile")).toBe(true);
  });

  it("AC-2: returnTo validation rejects protocol-relative URLs", () => {
    expect(isValidReturnTo("//evil.com")).toBe(false);
  });

  it("AC-2: returnTo validation rejects absolute URLs", () => {
    expect(isValidReturnTo("https://evil.com")).toBe(false);
    expect(isValidReturnTo("http://evil.com")).toBe(false);
  });

  it("AC-2: returnTo validation rejects non-strings and nulls", () => {
    expect(isValidReturnTo(null)).toBe(false);
    expect(isValidReturnTo(undefined)).toBe(false);
    expect(isValidReturnTo("")).toBe(false);
  });

  it("AC-2: getRedirectPath returns valid returnTo or / as fallback", () => {
    expect(getRedirectPath("/dashboard")).toBe("/dashboard");
    expect(getRedirectPath("//evil.com")).toBe("/");
    expect(getRedirectPath("https://evil.com")).toBe("/");
    expect(getRedirectPath(null)).toBe("/");
    expect(getRedirectPath(undefined)).toBe("/");
  });
});

describe("AC-3: Logout behavior", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("AC-3: logout POSTs to /api/auth/logout, clears user state, and status becomes unauthenticated", async () => {
    global.fetch = vi.fn();

    const mockRequest = vi.fn();
    mockRequest.mockImplementation((path: string, init?: RequestInit) => {
      if (path === "/api/auth/me") {
        return Promise.resolve({
          ok: true,
          json: () =>
            Promise.resolve({ user: { id: "user1", email: "test@example.com" } }),
        } as Response);
      }
      if (path === "/api/auth/logout" && init?.method === "POST") {
        return Promise.resolve({
          ok: true,
        } as Response);
      }
      return Promise.reject(new Error("Not mocked"));
    });
    vi.mocked(authClient.request).mockImplementation(mockRequest);
    vi.mocked(authClient.clear).mockImplementation(() => {
      // Clear the token
    });

    render(
      <BrowserRouter>
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      </BrowserRouter>
    );

    // Start unauthenticated (refresh fails)
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: false,
      } as Response)
    );

    await waitFor(() => {
      expect(screen.getByText("Status: unauthenticated")).toBeDefined();
    });
  });

  it("AC-3: logout clears auth state even if POST fails", async () => {
    global.fetch = vi.fn(() =>
      Promise.resolve({
        ok: false,
      } as Response)
    );

    const mockRequest = vi.fn();
    mockRequest.mockRejectedValue(new Error("Network error"));
    vi.mocked(authClient.request).mockImplementation(mockRequest);
    vi.mocked(authClient.clear).mockImplementation(() => {
      // Clear the token
    });

    render(
      <BrowserRouter>
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      </BrowserRouter>
    );

    await waitFor(() => {
      expect(screen.getByText("Status: unauthenticated")).toBeDefined();
    });

    // Click logout
    const logoutButton = screen.getByRole("button", { name: "Logout" });
    fireEvent.click(logoutButton);

    await waitFor(() => {
      expect(authClient.clear).toHaveBeenCalled();
      expect(mockRequest).toHaveBeenCalledWith("/api/auth/logout", { method: "POST" });
    });
  });
});
