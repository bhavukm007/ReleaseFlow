import type { Team, TeamRole } from "../types";
import { api } from "./client";

export const teamApi = {
  list: async () => (await api.get<Team[]>("/teams")).data,
  get: async (id: string) => (await api.get<Team>(`/teams/${id}`)).data,
  create: async (name: string) => (await api.post<Team>("/teams", { name })).data,
  invite: async (id: string, email: string, role: TeamRole) => (await api.post(`/teams/${id}/invitations`, { email, role })).data,
  remove: async (id: string, userId: string) => { await api.delete(`/teams/${id}/members/${userId}`); },
  transfer: async (id: string, userId: string) => (await api.post<Team>(`/teams/${id}/transfer`, { user_id: userId })).data,
  delete: async (id: string) => { await api.delete(`/teams/${id}`); },
};
