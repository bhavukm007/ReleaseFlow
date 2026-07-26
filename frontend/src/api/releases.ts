import axios from "axios";
import type { Release, ReleaseInput } from "../types";

const api = axios.create({ baseURL: import.meta.env.VITE_API_URL ?? "http://localhost:8000", timeout: 10000 });
export const releaseApi = {
  list: async () => (await api.get<Release[]>("/releases")).data,
  get: async (id: number) => (await api.get<Release>(`/releases/${id}`)).data,
  create: async (input: ReleaseInput) => (await api.post<Release>("/releases", input)).data,
  updateSteps: async (id: number, steps: Record<string, boolean>) => (await api.patch<Release>(`/releases/${id}/steps`, { steps })).data,
  updateInfo: async (id: number, additional_info: string | null) => (await api.patch<Release>(`/releases/${id}/info`, { additional_info })).data,
  delete: async (id: number) => { await api.delete(`/releases/${id}`); },
};
