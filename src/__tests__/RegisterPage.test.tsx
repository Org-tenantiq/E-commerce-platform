import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import RegisterPage from "../pages/RegisterPage";
import { authClient } from "../api/authClient";

vi.mock("../api/authClient");

describe("RegisterPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.clearAllMocks();
  });

  it("AC-1: renders with labelled email and password inputs and submit button, calls authClient.register on valid input", async () => {
    vi.mocked(authClient.register).mockResolvedValueOnce(undefined);

    render(<RegisterPage />);

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
    render(<RegisterPage />);

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
    render(<RegisterPage />);

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

    render(<RegisterPage />);

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
});
