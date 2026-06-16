import * as SecureStore from "expo-secure-store";
import {
  createContext, useContext, useEffect, useState, type ReactNode,
} from "react";
import { api, setAuthToken } from "../api/client";
import type { UserOut } from "../api/types";

const TOKEN_KEY = "helfy_token";

export type Session = {
  ready: boolean;
  user: UserOut | null;
  signIn: (token: string) => Promise<void>;
  signOut: () => Promise<void>;
};

export const SessionContext = createContext<Session | null>(null);

export function useSession(): Session {
  const ctx = useContext(SessionContext);
  if (!ctx) throw new Error("useSession deve ser usado dentro de SessionProvider");
  return ctx;
}

export function SessionProvider({ children }: { children: ReactNode }) {
  const [ready, setReady] = useState(false);
  const [user, setUser] = useState<UserOut | null>(null);

  async function loadUser(token: string): Promise<void> {
    setAuthToken(token);
    try {
      setUser(await api<UserOut>("/auth/me"));
    } catch {
      setAuthToken(null);
      await SecureStore.deleteItemAsync(TOKEN_KEY);
      setUser(null);
    }
  }

  useEffect(() => {
    (async () => {
      const token = await SecureStore.getItemAsync(TOKEN_KEY);
      if (token) await loadUser(token);
      setReady(true);
    })();
  }, []);

  async function signIn(token: string) {
    await SecureStore.setItemAsync(TOKEN_KEY, token);
    await loadUser(token);
  }

  async function signOut() {
    await SecureStore.deleteItemAsync(TOKEN_KEY);
    setAuthToken(null);
    setUser(null);
  }

  return (
    <SessionContext.Provider value={{ ready, user, signIn, signOut }}>
      {children}
    </SessionContext.Provider>
  );
}
