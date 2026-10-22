export function validateEmail(email: string): string | null {
  if (!email.includes("@")) {
    return "Invalid email";
  }
  return null;
}

export function validatePassword(password: string): string | null {
  if (password.length < 8) {
    return "Password must be at least 8 characters";
  }
  return null;
}
