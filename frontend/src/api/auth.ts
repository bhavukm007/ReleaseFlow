import type { User } from "../types";
import { api } from "./client";

export interface AuthResult { access_token: string; expires_at: string; user: User }
export const authApi = {
  health: async () => { await api.get("/health"); },
  signup: async (input: { full_name: string; email: string; password: string }) => (await api.post<AuthResult>("/auth/signup", input)).data,
  login: async (input: { email: string; password: string }) => (await api.post<AuthResult>("/auth/login", input)).data,
  refresh: async () => (await api.post<AuthResult>("/auth/refresh")).data,
  me: async () => (await api.get<User>("/auth/me")).data,
  logout: async () => { await api.post("/auth/logout"); },
};
