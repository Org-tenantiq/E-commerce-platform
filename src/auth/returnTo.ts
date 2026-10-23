export function isValidReturnTo(returnTo: string | null | undefined): returnTo is string {
  if (!returnTo || typeof returnTo !== "string") return false;
  // Only allow relative paths starting with a single "/"
  // Reject "//" (protocol-relative) and absolute URLs
  if (!returnTo.startsWith("/")) return false;
  if (returnTo.startsWith("//")) return false;
  // Check if it looks like an absolute URL (contains :// after the first /)
  if (returnTo.includes("://")) return false;
  return true;
}

export function getRedirectPath(returnTo: string | null | undefined): string {
  return isValidReturnTo(returnTo) ? returnTo : "/";
}
