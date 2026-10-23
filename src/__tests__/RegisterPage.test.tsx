import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { BrowserRouter, MemoryRouter, Routes, Route } from "react-router-dom";
import RegisterPage from "../pages/RegisterPage";
import { authClient } from "../api/authClient";

vi.mock("../api/authClient");

// Test component to track navigation
function TestPage() {
  return <div>Test Page</div>;
}

describe("RegisterPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("AC-1: renders with labelled email and password inputs and submit button, calls authClient.register on valid input", async () => {
    vi.mocked(authClient.register).mockResolvedValueOnce(undefined);

    render(
      <BrowserRouter>
        <RegisterPage />
      </BrowserRouter>
    );

    const emailLabel = screen.getByText("Email");
    const passwordLabel = screen.getByText("Password");
    expect(emailLabel).toBeDefined();
    expect(passwordLabel).toBeDefined();

    const emailInput = screen.getByLabelText("Email") as HTMLInputElement;
    const passwordInput = screen.getByLabelText("Password") as HTMLInputElement;
    const form = screen.getByRole("button", { name: /Register/i }).closest("form") as HTMLFormElement;

    expect(emailInput).toBeDefined();
    expect(passwordInput).toBeDefined();
    expect(form).toBeDefined();

    fireEvent.change(emailInput, { target: { value: "test@example.com" } });
    fireEvent.change(passwordInput, { target: { value: "password123" } });
    fireEvent.submit(form);

    await waitFor(() => {
      expect(authClient.register).toHaveBeenCalledWith("test@example.com", "password123");
    });
  });

  it("AC-2: invalid email shows error with aria-invalid and aria-describedby", async () => {
    render(
      <BrowserRouter>
        <RegisterPage />
      </BrowserRouter>
    );

    const emailInput = screen.getByLabelText("Email") as HTMLInputElement;
    const passwordInput = screen.getByLabelText("Password") as HTMLInputElement;
    const form = screen.getByRole("button", { name: /Register/i }).closest("form") as HTMLFormElement;

    fireEvent.change(emailInput, { target: { value: "invalid-email" } });
    fireEvent.change(passwordInput, { target: { value: "password123" } });
    fireEvent.submit(form);

    await waitFor(() => {
      const updatedEmailInput = screen.getByLabelText("Email") as HTMLInputElement;
      expect(updatedEmailInput.getAttribute("aria-invalid")).toBe("true");
      expect(updatedEmailInput.getAttribute("aria-describedby")).toBe("email-error");
      expect(screen.getByText("Invalid email")).toBeDefined();
    });

    expect(authClient.register).not.toHaveBeenCalled();
  });

  it("AC-2: password under 8 characters shows error with aria-invalid and aria-describedby", async () => {
    render(
      <BrowserRouter>
        <RegisterPage />
      </BrowserRouter>
    );

    const emailInput = screen.getByLabelText("Email") as HTMLInputElement;
    const passwordInput = screen.getByLabelText("Password") as HTMLInputElement;
    const form = screen.getByRole("button", { name: /Register/i }).closest("form") as HTMLFormElement;

    fireEvent.change(emailInput, { target: { value: "test@example.com" } });
    fireEvent.change(passwordInput, { target: { value: "pass" } });
    fireEvent.submit(form);

    await waitFor(() => {
      const updatedPasswordInput = screen.getByLabelText("Password") as HTMLInputElement;
      expect(updatedPasswordInput.getAttribute("aria-invalid")).toBe("true");
      expect(updatedPasswordInput.getAttribute("aria-describedby")).toBe("password-error");
      expect(screen.getByText("Password must be at least 8 characters")).toBeDefined();
    });

    expect(authClient.register).not.toHaveBeenCalled();
  });

  it("AC-3: API returns 409 shows 'Email already registered'", async () => {
    vi.mocked(authClient.register).mockRejectedValueOnce({ status: 409 });

    render(
      <BrowserRouter>
        <RegisterPage />
      </BrowserRouter>
    );

    const emailInput = screen.getByLabelText("Email") as HTMLInputElement;
    const passwordInput = screen.getByLabelText("Password") as HTMLInputElement;
    const form = screen.getByRole("button", { name: /Register/i }).closest("form") as HTMLFormElement;

    fireEvent.change(emailInput, { target: { value: "test@example.com" } });
    fireEvent.change(passwordInput, { target: { value: "password123" } });
    fireEvent.submit(form);

    await waitFor(() => {
      expect(screen.getByText("Email already registered")).toBeDefined();
    });
  });

  it("AC-3: after successful registration, redirects to returnTo query parameter", async () => {
    vi.mocked(authClient.register).mockResolvedValueOnce(undefined);

    render(
      <MemoryRouter initialEntries={["/register?returnTo=%2Fdashboard"]}>
        <Routes>
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/dashboard" element={<TestPage />} />
        </Routes>
      </MemoryRouter>
    );

    // Initially should show register form
    await waitFor(() => {
      expect(screen.getByRole("heading", { name: /Register/i })).toBeDefined();
    });

    const emailInput = screen.getByLabelText("Email") as HTMLInputElement;
    const passwordInput = screen.getByLabelText("Password") as HTMLInputElement;
    const form = screen.getByRole("button", { name: /Register/i }).closest("form") as HTMLFormElement;

    fireEvent.change(emailInput, { target: { value: "test@example.com" } });
    fireEvent.change(passwordInput, { target: { value: "password123" } });
    fireEvent.submit(form);

    // After successful registration, should navigate to returnTo page (/dashboard)
    await waitFor(() => {
      expect(screen.getByText("Test Page")).toBeDefined();
      expect(screen.queryByRole("heading", { name: /Register/i })).toBeNull();
    });

    expect(authClient.register).toHaveBeenCalledWith("test@example.com", "password123");
  });

  it("AC-3: after successful registration without returnTo, redirects to /", async () => {
    vi.mocked(authClient.register).mockResolvedValueOnce(undefined);

    render(
      <MemoryRouter initialEntries={["/register"]}>
        <Routes>
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/" element={<TestPage />} />
        </Routes>
      </MemoryRouter>
    );

    // Initially should show register form
    await waitFor(() => {
      expect(screen.getByRole("heading", { name: /Register/i })).toBeDefined();
    });

    const emailInput = screen.getByLabelText("Email") as HTMLInputElement;
    const passwordInput = screen.getByLabelText("Password") as HTMLInputElement;
    const form = screen.getByRole("button", { name: /Register/i }).closest("form") as HTMLFormElement;

    fireEvent.change(emailInput, { target: { value: "test@example.com" } });
    fireEvent.change(passwordInput, { target: { value: "password123" } });
    fireEvent.submit(form);

    // After successful registration without returnTo, should navigate to / (home)
    await waitFor(() => {
      expect(screen.getByText("Test Page")).toBeDefined();
      expect(screen.queryByRole("heading", { name: /Register/i })).toBeNull();
    });

    expect(authClient.register).toHaveBeenCalledWith("test@example.com", "password123");
  });
});
