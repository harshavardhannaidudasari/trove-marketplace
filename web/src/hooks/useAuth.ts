import { useCallback, useEffect, useState } from "react";
import { authApi } from "../api/auth";
import { useAuthStore } from "../store/authStore";
import { useCartStore } from "../store/cartStore";

export function useAuthBootstrap() {
  const [ready, setReady] = useState(false);
  const accessToken = useAuthStore((s) => s.accessToken);
  const setUser = useAuthStore((s) => s.setUser);
  const clearAuth = useAuthStore((s) => s.clearAuth);
  const fetchCart = useCartStore((s) => s.fetch);

  useEffect(() => {
    let cancelled = false;
    async function bootstrap() {
      if (!accessToken) {
        setReady(true);
        return;
      }
      try {
        const user = await authApi.me();
        if (cancelled) return;
        setUser(user);
        await fetchCart();
      } catch {
        if (!cancelled) clearAuth();
      } finally {
        if (!cancelled) setReady(true);
      }
    }
    bootstrap();
    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return ready;
}

export function useAuth() {
  const user = useAuthStore((s) => s.user);
  const setTokens = useAuthStore((s) => s.setTokens);
  const setUser = useAuthStore((s) => s.setUser);
  const clearAuth = useAuthStore((s) => s.clearAuth);
  const fetchCart = useCartStore((s) => s.fetch);
  const resetCart = useCartStore((s) => s.reset);

  const login = useCallback(
    async (email: string, password: string) => {
      const tokens = await authApi.login(email, password);
      setTokens(tokens.access_token, tokens.refresh_token);
      const me = await authApi.me();
      setUser(me);
      await fetchCart();
    },
    [setTokens, setUser, fetchCart]
  );

  const register = useCallback(
    async (email: string, password: string, fullName: string) => {
      const tokens = await authApi.register(email, password, fullName);
      setTokens(tokens.access_token, tokens.refresh_token);
      const me = await authApi.me();
      setUser(me);
      await fetchCart();
    },
    [setTokens, setUser, fetchCart]
  );

  const logout = useCallback(() => {
    clearAuth();
    resetCart();
  }, [clearAuth, resetCart]);

  return { user, isAuthenticated: !!user, login, register, logout };
}
