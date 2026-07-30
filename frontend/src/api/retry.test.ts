import { AxiosError } from "axios";
import { afterEach, expect, it, vi } from "vitest";
import {
  COLD_START_MAX_ATTEMPTS,
  isRetryableApiError,
  retryDelay,
  shouldRetryQuery,
  withColdStartRetry,
} from "./retry";

afterEach(() => vi.useRealTimers());

it("uses capped exponential backoff", () => {
  expect([0, 1, 2, 3, 4, 5].map(retryDelay)).toEqual([1_000, 2_000, 4_000, 8_000, 16_000, 30_000]);
});

it("retries network, timeout, cold-start HTML, and transient server errors only", () => {
  expect(isRetryableApiError(new AxiosError("network", "ERR_NETWORK"))).toBe(true);
  expect(isRetryableApiError(new AxiosError("timeout", "ECONNABORTED"))).toBe(true);
  expect(isRetryableApiError(new AxiosError("html", "ERR_COLD_START"))).toBe(true);
  expect(isRetryableApiError(new AxiosError("bad request", undefined, undefined, undefined, { status: 400 } as never))).toBe(false);
  expect(shouldRetryQuery(COLD_START_MAX_ATTEMPTS - 1, new AxiosError("network"))).toBe(false);
});

it("recovers automatically when the fourth attempt succeeds", async () => {
  vi.useFakeTimers();
  const operation = vi.fn()
    .mockRejectedValueOnce(new AxiosError("offline", "ERR_NETWORK"))
    .mockRejectedValueOnce(new AxiosError("offline", "ERR_NETWORK"))
    .mockRejectedValueOnce(new AxiosError("offline", "ERR_NETWORK"))
    .mockResolvedValue("ready");
  const retries = vi.fn();

  const result = withColdStartRetry(operation, retries);
  await vi.runAllTimersAsync();

  await expect(result).resolves.toBe("ready");
  expect(operation).toHaveBeenCalledTimes(4);
  expect(retries).toHaveBeenCalledTimes(3);
});
