import axios, { AxiosError } from "axios";

const baseURL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";
const configuredTimeout = Number(import.meta.env.VITE_API_TIMEOUT_MS ?? 25_000);
export const api = axios.create({
  baseURL,
  timeout: Number.isFinite(configuredTimeout) && configuredTimeout >= 5_000 ? configuredTimeout : 25_000,
  withCredentials: true,
});
let accessToken: string | null = null;
let refreshPromise: Promise<string> | null = null;

export function setAccessToken(token: string | null) { accessToken = token; }
export function getAccessToken() { return accessToken; }

api.interceptors.request.use((config) => {
  if (accessToken) config.headers.Authorization = `Bearer ${accessToken}`;
  return config;
});

api.interceptors.response.use((response) => {
  const contentType = String(response.headers["content-type"] ?? "");
  if (contentType.includes("text/html")) {
    return Promise.reject(new AxiosError(
      "The API is starting and returned a temporary HTML response",
      "ERR_COLD_START",
      response.config,
      response.request,
      response,
    ));
  }
  return response;
});

api.interceptors.response.use(undefined, async (error) => {
  const request = error.config;
  if (error.response?.status !== 401 || request?._retried || request?.url?.includes("/auth/")) throw error;
  request._retried = true;
  refreshPromise ??= api.post<{ access_token: string }>("/auth/refresh").then(({ data }) => {
    setAccessToken(data.access_token);
    return data.access_token;
  }).finally(() => { refreshPromise = null; });
  const token = await refreshPromise;
  request.headers.Authorization = `Bearer ${token}`;
  return api(request);
});

export function websocketUrl(token: string) {
  const url = new URL(baseURL);
  url.protocol = url.protocol === "https:" ? "wss:" : "ws:";
  url.pathname = "/ws";
  url.searchParams.set("token", token);
  return url.toString();
}
