import type { Activity, CollaboratorInput, Release, ReleaseInput } from "../types";
import { api } from "./client";

export const releaseApi = {
  list: async (teamId?: string | null) => (await api.get<Release[]>("/releases", { params: teamId ? { team_id: teamId } : undefined })).data,
  get: async (id: number) => (await api.get<Release>(`/releases/${id}`)).data,
  create: async (input: ReleaseInput) => (await api.post<Release>("/releases", input)).data,
  update: async (id: number, input: Pick<ReleaseInput, "name" | "due_date" | "additional_info">) => (await api.put<Release>(`/releases/${id}`, input)).data,
  updateSteps: async (id: number, steps: Record<string, boolean>) => (await api.patch<Release>(`/releases/${id}/steps`, { steps })).data,
  updateChecklist: async (id: number, steps: Record<string, boolean>) => (await api.patch<Release>(`/releases/${id}/checklist`, { items: Object.entries(steps).map(([name, completed]) => ({ name, completed })) })).data,
  updateInfo: async (id: number, additional_info: string | null) => (await api.patch<Release>(`/releases/${id}/info`, { additional_info })).data,
  activities: async (id: number) => (await api.get<Activity[]>(`/releases/${id}/activities`)).data,
  recentActivities: async () => (await api.get<Activity[]>("/activities", { params: { limit: 6 } })).data,
  addCollaborator: async (id: number, collaborator: CollaboratorInput) => (await api.post<Release>(`/releases/${id}/collaborators`, collaborator)).data,
  updateCollaborator: async (id: number, userId: string, role: CollaboratorInput["role"]) => (await api.patch<Release>(`/releases/${id}/collaborators/${userId}`, { role })).data,
  removeCollaborator: async (id: number, userId: string) => (await api.delete<Release>(`/releases/${id}/collaborators/${userId}`)).data,
  delete: async (id: number) => { await api.delete(`/releases/${id}`); },
};
