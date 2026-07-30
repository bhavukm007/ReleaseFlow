import { render, waitFor } from "@testing-library/react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { expect, it, vi } from "vitest";
import { useRealtime } from "./useRealtime";

vi.mock("../api/client", () => ({
  getAccessToken: () => "access-token",
  websocketUrl: () => "ws://localhost/ws?token=access-token",
}));

class MockWebSocket {
  static OPEN = 1;
  static instances: MockWebSocket[] = [];
  readyState = 1;
  onmessage: (() => void) | null = null;
  send = vi.fn();
  close = vi.fn();
  constructor(public url: string) { MockWebSocket.instances.push(this); }
}

function Consumer() {
  useRealtime();
  return null;
}

it("invalidates cached workspace data after a realtime event", async () => {
  const client = new QueryClient();
  const invalidate = vi.spyOn(client, "invalidateQueries");
  vi.stubGlobal("WebSocket", MockWebSocket);
  render(<QueryClientProvider client={client}><Consumer /></QueryClientProvider>);
  MockWebSocket.instances.at(-1)?.onmessage?.();
  await waitFor(() => expect(invalidate).toHaveBeenCalledWith({ queryKey: ["releases"] }));
  expect(invalidate).toHaveBeenCalledWith({ queryKey: ["teams"] });
  vi.unstubAllGlobals();
});
