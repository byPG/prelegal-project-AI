"use client";

import { createContext, useContext, useEffect, useState } from "react";
import { fetchCurrentUser, signIn as apiSignIn, signUp as apiSignUp } from "@/lib/api";
import type { User } from "@/types/auth";

const TOKEN_STORAGE_KEY = "prelegal_token";

type AuthStatus = "loading" | "authenticated" | "unauthenticated";

interface AuthContextValue {
  status: AuthStatus;
  user: User | null;
  token: string | null;
  signIn: (email: string, password: string) => Promise<void>;
  signUp: (email: string, password: string) => Promise<void>;
  signOut: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [status, setStatus] = useState<AuthStatus>("loading");
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    const storedToken = window.localStorage.getItem(TOKEN_STORAGE_KEY);
    if (!storedToken) {
      setStatus("unauthenticated");
      return;
    }

    let cancelled = false;
    fetchCurrentUser(storedToken)
      .then((fetchedUser) => {
        if (cancelled) return;
        setToken(storedToken);
        setUser(fetchedUser);
        setStatus("authenticated");
      })
      .catch(() => {
        if (cancelled) return;
        window.localStorage.removeItem(TOKEN_STORAGE_KEY);
        setStatus("unauthenticated");
      });

    return () => {
      cancelled = true;
    };
  }, []);

  async function signIn(email: string, password: string) {
    const { access_token } = await apiSignIn(email, password);
    const fetchedUser = await fetchCurrentUser(access_token);
    window.localStorage.setItem(TOKEN_STORAGE_KEY, access_token);
    setToken(access_token);
    setUser(fetchedUser);
    setStatus("authenticated");
  }

  async function signUp(email: string, password: string) {
    await apiSignUp(email, password);
    await signIn(email, password);
  }

  function signOut() {
    window.localStorage.removeItem(TOKEN_STORAGE_KEY);
    setToken(null);
    setUser(null);
    setStatus("unauthenticated");
  }

  return (
    <AuthContext.Provider value={{ status, user, token, signIn, signUp, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) throw new Error("useAuth must be used within an AuthProvider");
  return context;
}
