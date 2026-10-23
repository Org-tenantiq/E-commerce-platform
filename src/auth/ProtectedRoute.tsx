import { Navigate } from "react-router-dom";
import { useAuth } from "./AuthProvider";
import { getRedirectPath } from "./returnTo";

interface ProtectedRouteProps {
  children: React.ReactNode;
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { status } = useAuth();

  if (status === "loading") {
    return <div>Loading...</div>;
  }

  if (status === "unauthenticated") {
    const currentPath = window.location.pathname + window.location.search;
    return <Navigate to={`/login?returnTo=${encodeURIComponent(currentPath)}`} replace />;
  }

  return children;
}
