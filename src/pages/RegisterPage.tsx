import { useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { authClient } from "../api/authClient";
import { validateEmail, validatePassword } from "../auth/validate";
import { getRedirectPath } from "../auth/returnTo";

export default function RegisterPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<{ email?: string; password?: string; server?: string }>({});
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const newErrors: typeof errors = {};

    const emailError = validateEmail(email);
    if (emailError) newErrors.email = emailError;

    const passwordError = validatePassword(password);
    if (passwordError) newErrors.password = passwordError;

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    setErrors({});
    setIsLoading(true);

    try {
      await authClient.register(email, password);
      const returnTo = searchParams.get("returnTo");
      const redirectPath = getRedirectPath(returnTo);
      navigate(redirectPath, { replace: true });
    } catch (err) {
      const error = err as { status?: number };
      if (error.status === 409) {
        setErrors({ server: "Email already registered" });
      } else {
        setErrors({ server: "Registration failed" });
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit}>
      <h1>Register</h1>
      {errors.server && <div>{errors.server}</div>}
      <div>
        <label htmlFor="email">Email</label>
        <input
          id="email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          {...(errors.email ? { "aria-invalid": "true", "aria-describedby": "email-error" } : {})}
        />
        {errors.email && <div id="email-error">{errors.email}</div>}
      </div>
      <div>
        <label htmlFor="password">Password</label>
        <input
          id="password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          {...(errors.password ? { "aria-invalid": "true", "aria-describedby": "password-error" } : {})}
        />
        {errors.password && <div id="password-error">{errors.password}</div>}
      </div>
      <button type="submit" disabled={isLoading}>
        {isLoading ? "Registering..." : "Register"}
      </button>
    </form>
  );
}
