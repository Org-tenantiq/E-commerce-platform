import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { useNavigate } from "react-router-dom";
import { authClient, AuthExpiredError } from "../api/authClient";

export interface User {
  id: string;
  email: string;
}

export type AuthStatus = "loading" | "authenticated" | "unauthenticated";

interface AuthContextType {
  user: User | null;
  status: AuthStatus;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const navigate = useNavigate();
  const [user, setUser] = useState<User | null>(null);
  const [status, setStatus] = useState<AuthStatus>("loading");

  useEffect(() => {
    const initAuth = async () => {
      try {
        // Attempt silent refresh first
        const refreshRes = await fetch("/api/auth/refresh", {
          method: "POST",
          credentials: "include",
        });

        if (refreshRes.ok) {
          // If refresh succeeded, load the user
          const meRes = await authClient.request("/api/auth/me");
          if (meRes.ok) {
            const data = (await meRes.json()) as { user?: User };
            setUser(data.user || null);
            setStatus(data.user ? "authenticated" : "unauthenticated");
          } else {
            setStatus("unauthenticated");
          }
        } else {
          setStatus("unauthenticated");
        }
      } catch (err) {
        if (err instanceof AuthExpiredError) {
          setStatus("unauthenticated");
        } else {
          console.error("Auth initialization failed:", err);
          setStatus("unauthenticated");
        }
      }
    };

    initAuth();
  }, []);

  const login = async (email: string, password: string) => {
    await authClient.login(email, password);
    // Load user after login
    const res = await authClient.request("/api/auth/me");
    if (res.ok) {
      const data = (await res.json()) as { user?: User };
      setUser(data.user || null);
      setStatus("authenticated");
    }
  };

  const logout = async () => {
    try {
      await authClient.request("/api/auth/logout", { method: "POST" });
    } catch (err) {
      console.error("Logout failed:", err);
    } finally {
      authClient.clear();
      setUser(null);
      setStatus("unauthenticated");
      navigate("/login", { replace: true });
    }
  };

  return (
    <AuthContext.Provider value={{ user, status, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
