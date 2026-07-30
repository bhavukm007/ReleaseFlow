import { createContext, useContext, useEffect, useMemo, useState, type ReactNode } from "react";
import { authApi } from "../api/auth";
import { setAccessToken } from "../api/client";
import { withColdStartRetry } from "../api/retry";
import type { User } from "../types";

interface AuthContextValue {
  user: User | null; loading: boolean; startingServer: boolean; startupError: boolean;
  login: (email: string, password: string) => Promise<void>;
  signup: (fullName: string, email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
}
const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [startingServer, setStartingServer] = useState(false);
  const [startupError, setStartupError] = useState(false);
  useEffect(() => {
    withColdStartRetry(authApi.health, () => setStartingServer(true))
      .then(authApi.refresh)
      .then((result) => { setAccessToken(result.access_token); setUser(result.user); })
      .catch((error: unknown) => {
        setAccessToken(null);
        if ((error as { response?: { status?: number } }).response?.status !== 401) setStartupError(true);
      })
      .finally(() => { setStartingServer(false); setLoading(false); });
  }, []);
  const value = useMemo<AuthContextValue>(() => ({
    user, loading, startingServer, startupError,
    login: async (email, password) => { const result = await authApi.login({ email, password }); setAccessToken(result.access_token); setUser(result.user); },
    signup: async (fullName, email, password) => { const result = await authApi.signup({ full_name: fullName, email, password }); setAccessToken(result.access_token); setUser(result.user); },
    logout: async () => { try { await authApi.logout(); } finally { setAccessToken(null); setUser(null); } },
  }), [user, loading, startingServer, startupError]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const value = useContext(AuthContext);
  if (!value) throw new Error("useAuth must be used inside AuthProvider");
  return value;
}
