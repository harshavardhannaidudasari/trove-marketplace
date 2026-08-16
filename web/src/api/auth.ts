import { api } from "./client";
import type { TokenPair, User } from "./types";

export const authApi = {
  register: (email: string, password: string, full_name: string) =>
    api.post<TokenPair>("/auth/register", { email, password, full_name }),

  login: (email: string, password: string) => {
    const body = new URLSearchParams();
    body.set("username", email);
    body.set("password", password);
    return api.postForm<TokenPair>("/auth/login", body);
  },

  me: () => api.get<User>("/auth/me", true),

  logout: () => api.post<void>("/auth/logout", undefined, true),
};
