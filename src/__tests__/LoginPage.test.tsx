import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { BrowserRouter, MemoryRouter, Routes, Route } from "react-router-dom";
import LoginPage from "../pages/LoginPage";
import { authClient } from "../api/authClient";

vi.mock("../api/authClient");

// Test component to track navigation
function TestPage() {
  return <div>Test Page</div>;
}

describe("LoginPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("AC-1: renders with labelled email and password inputs and submit button, calls authClient.login on valid input", async () => {
    vi.mocked(authClient.login).mockResolvedValueOnce(undefined);

    render(
      <BrowserRouter>
        <LoginPage />
      </BrowserRouter>
    );

    const emailLabel = screen.getByText("Email");
    const passwordLabel = screen.getByText("Password");
    expect(emailLabel).toBeDefined();
    expect(passwordLabel).toBeDefined();

    const emailInput = screen.getByLabelText("Email") as HTMLInputElement;
    const passwordInput = screen.getByLabelText("Password") as HTMLInputElement;
    const form = screen.getByRole("button", { name: /Login/i }).closest("form") as HTMLFormElement;

    expect(emailInput).toBeDefined();
    expect(passwordInput).toBeDefined();
    expect(form).toBeDefined();

    fireEvent.change(emailInput, { target: { value: "test@example.com" } });
    fireEvent.change(passwordInput, { target: { value: "password123" } });
    fireEvent.submit(form);

    await waitFor(() => {
      expect(authClient.login).toHaveBeenCalledWith("test@example.com", "password123");
    });
  });

  it("AC-2: invalid email shows error with aria-invalid and aria-describedby", async () => {
    render(
      <BrowserRouter>
        <LoginPage />
      </BrowserRouter>
    );

    const emailInput = screen.getByLabelText("Email") as HTMLInputElement;
    const passwordInput = screen.getByLabelText("Password") as HTMLInputElement;
    const form = screen.getByRole("button", { name: /Login/i }).closest("form") as HTMLFormElement;

    fireEvent.change(emailInput, { target: { value: "invalid-email" } });
    fireEvent.change(passwordInput, { target: { value: "password123" } });
    fireEvent.submit(form);

    await waitFor(() => {
      const updatedEmailInput = screen.getByLabelText("Email") as HTMLInputElement;
      expect(updatedEmailInput.getAttribute("aria-invalid")).toBe("true");
      expect(updatedEmailInput.getAttribute("aria-describedby")).toBe("email-error");
      expect(screen.getByText("Invalid email")).toBeDefined();
    });

    expect(authClient.login).not.toHaveBeenCalled();
  });

  it("AC-2: password under 8 characters shows error with aria-invalid and aria-describedby", async () => {
    render(
      <BrowserRouter>
        <LoginPage />
      </BrowserRouter>
    );

    const emailInput = screen.getByLabelText("Email") as HTMLInputElement;
    const passwordInput = screen.getByLabelText("Password") as HTMLInputElement;
    const form = screen.getByRole("button", { name: /Login/i }).closest("form") as HTMLFormElement;

    fireEvent.change(emailInput, { target: { value: "test@example.com" } });
    fireEvent.change(passwordInput, { target: { value: "pass" } });
    fireEvent.submit(form);

    await waitFor(() => {
      const updatedPasswordInput = screen.getByLabelText("Password") as HTMLInputElement;
      expect(updatedPasswordInput.getAttribute("aria-invalid")).toBe("true");
      expect(updatedPasswordInput.getAttribute("aria-describedby")).toBe("password-error");
      expect(screen.getByText("Password must be at least 8 characters")).toBeDefined();
    });

    expect(authClient.login).not.toHaveBeenCalled();
  });

  it("AC-3: API returns 401 shows 'Invalid email or password'", async () => {
    vi.mocked(authClient.login).mockRejectedValueOnce({ status: 401 });

    render(
      <BrowserRouter>
        <LoginPage />
      </BrowserRouter>
    );

    const emailInput = screen.getByLabelText("Email") as HTMLInputElement;
    const passwordInput = screen.getByLabelText("Password") as HTMLInputElement;
    const form = screen.getByRole("button", { name: /Login/i }).closest("form") as HTMLFormElement;

    fireEvent.change(emailInput, { target: { value: "test@example.com" } });
    fireEvent.change(passwordInput, { target: { value: "password123" } });
    fireEvent.submit(form);

    await waitFor(() => {
      expect(screen.getByText("Invalid email or password")).toBeDefined();
    });
  });

  it("AC-3: after successful login, redirects to returnTo query parameter", async () => {
    vi.mocked(authClient.login).mockResolvedValueOnce(undefined);

    render(
      <MemoryRouter initialEntries={["/login?returnTo=%2Fdashboard"]}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/dashboard" element={<TestPage />} />
        </Routes>
      </MemoryRouter>
    );

    // Initially should show login form
    await waitFor(() => {
      expect(screen.getByRole("heading", { name: /Login/i })).toBeDefined();
    });

    const emailInput = screen.getByLabelText("Email") as HTMLInputElement;
    const passwordInput = screen.getByLabelText("Password") as HTMLInputElement;
    const form = screen.getByRole("button", { name: /Login/i }).closest("form") as HTMLFormElement;

    fireEvent.change(emailInput, { target: { value: "test@example.com" } });
    fireEvent.change(passwordInput, { target: { value: "password123" } });
    fireEvent.submit(form);

    // After successful login, should navigate to returnTo page (/dashboard)
    await waitFor(() => {
      expect(screen.getByText("Test Page")).toBeDefined();
      expect(screen.queryByRole("heading", { name: /Login/i })).toBeNull();
    });

    expect(authClient.login).toHaveBeenCalledWith("test@example.com", "password123");
  });

  it("AC-3: after successful login without returnTo, redirects to /", async () => {
    vi.mocked(authClient.login).mockResolvedValueOnce(undefined);

    render(
      <MemoryRouter initialEntries={["/login"]}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/" element={<TestPage />} />
        </Routes>
      </MemoryRouter>
    );

    // Initially should show login form
    await waitFor(() => {
      expect(screen.getByRole("heading", { name: /Login/i })).toBeDefined();
    });

    const emailInput = screen.getByLabelText("Email") as HTMLInputElement;
    const passwordInput = screen.getByLabelText("Password") as HTMLInputElement;
    const form = screen.getByRole("button", { name: /Login/i }).closest("form") as HTMLFormElement;

    fireEvent.change(emailInput, { target: { value: "test@example.com" } });
    fireEvent.change(passwordInput, { target: { value: "password123" } });
    fireEvent.submit(form);

    // After successful login without returnTo, should navigate to / (home)
    await waitFor(() => {
      expect(screen.getByText("Test Page")).toBeDefined();
      expect(screen.queryByRole("heading", { name: /Login/i })).toBeNull();
    });

    expect(authClient.login).toHaveBeenCalledWith("test@example.com", "password123");
  });
});
