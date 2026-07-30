import axios from "axios";

// Render Free services can take about a minute to wake. Seven attempts provide
// a 61-second backoff window when the proxy fails quickly, while request
// timeouts cover the more common case where Render holds the first request.
export const COLD_START_MAX_ATTEMPTS = 7;
export const COLD_START_BASE_DELAY_MS = 1_000;
export const COLD_START_MAX_DELAY_MS = 30_000;

export function isRetryableApiError(error: unknown): boolean {
  if (!axios.isAxiosError(error)) return false;
  if (error.code === "ERR_COLD_START") return true;
  if (!error.response) return true;
  return [408, 425, 429, 500, 502, 503, 504].includes(error.response.status);
}

export function retryDelay(attemptIndex: number): number {
  return Math.min(COLD_START_BASE_DELAY_MS * 2 ** attemptIndex, COLD_START_MAX_DELAY_MS);
}

export function shouldRetryQuery(failureCount: number, error: unknown): boolean {
  return failureCount < COLD_START_MAX_ATTEMPTS - 1 && isRetryableApiError(error);
}

export async function withColdStartRetry<T>(
  operation: () => Promise<T>,
  onRetry?: (attempt: number) => void,
): Promise<T> {
  let lastError: unknown;
  for (let attempt = 1; attempt <= COLD_START_MAX_ATTEMPTS; attempt += 1) {
    try {
      return await operation();
    } catch (error) {
      lastError = error;
      if (!isRetryableApiError(error) || attempt === COLD_START_MAX_ATTEMPTS) throw error;
      onRetry?.(attempt + 1);
      await new Promise((resolve) => window.setTimeout(resolve, retryDelay(attempt - 1)));
    }
  }
  throw lastError;
}
