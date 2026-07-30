import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { beforeEach, expect, it, vi } from "vitest";
import { AxiosError } from "axios";
import { releaseApi } from "../api/releases";
import { STEP_NAMES, type Release } from "../types";
import { HomePage } from "./HomePage";
import { WorkspaceProvider } from "../contexts/WorkspaceContext";

vi.mock("../api/releases", () => ({
  releaseApi: {
    list: vi.fn(),
    create: vi.fn(),
    recentActivities: vi.fn(),
  },
}));

const release: Release = {
  id: 1,
  name: "Web Launch",
  due_date: "2026-08-20",
  additional_info: null,
  steps: Object.fromEntries(STEP_NAMES.map((name) => [name, false])),
  status: "planned",
  completed_steps: 0,
  total_steps: 8,
  created_at: "2026-07-26T00:00:00Z",
  updated_at: "2026-07-26T00:00:00Z",
  owner_id: "00000000-0000-0000-0000-000000000001",
  team_id: null,
  access_role: "owner",
  collaborators: [{ user_id: "00000000-0000-0000-0000-000000000001", full_name: "Test User", email: "test@example.com", role: "owner" }],
};

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(releaseApi.list).mockResolvedValue([release]);
  vi.mocked(releaseApi.recentActivities).mockResolvedValue([]);
  vi.mocked(releaseApi.create).mockResolvedValue({ ...release, id: 2, name: "API Launch" });
});

it("loads releases and creates a new release through the modal", async () => {
  const user = userEvent.setup();
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(<QueryClientProvider client={queryClient}><WorkspaceProvider><MemoryRouter><HomePage /></MemoryRouter></WorkspaceProvider></QueryClientProvider>);

  expect(await screen.findByText("Web Launch")).toBeInTheDocument();
  await user.click(screen.getByRole("button", { name: "New release" }));
  await user.type(screen.getByLabelText("Release name"), "API Launch");
  await user.type(screen.getByLabelText("Due date"), "2026-08-21");
  await user.click(screen.getByRole("button", { name: "Add teammate" }));
  await user.type(screen.getByLabelText("Teammate email 1"), "admin@example.com");
  await user.selectOptions(screen.getByLabelText("Teammate role 1"), "admin");
  await user.click(screen.getByRole("button", { name: "Create release" }));

  await waitFor(() => expect(releaseApi.create).toHaveBeenCalled());
  expect(vi.mocked(releaseApi.create).mock.calls[0][0]).toEqual(expect.objectContaining({
    name: "API Launch", due_date: "2026-08-21", additional_info: null, team_id: null,
    collaborators: [{ email: "admin@example.com", role: "admin" }],
  }));
  expect(await screen.findByText("Release created")).toBeInTheDocument();
});

it("shows a server-starting state and recovers without manual retry", async () => {
  vi.mocked(releaseApi.list)
    .mockRejectedValueOnce(new AxiosError("cold", "ERR_NETWORK"))
    .mockRejectedValueOnce(new AxiosError("cold", "ERR_NETWORK"))
    .mockResolvedValueOnce([release]);
  const queryClient = new QueryClient({ defaultOptions: { queries: {
    retry: (failureCount) => failureCount < 2,
    retryDelay: 100,
  } } });
  render(<QueryClientProvider client={queryClient}><WorkspaceProvider><MemoryRouter><HomePage /></MemoryRouter></WorkspaceProvider></QueryClientProvider>);

  expect(await screen.findByText("Starting server...")).toBeInTheDocument();
  expect(await screen.findByText("Web Launch")).toBeInTheDocument();
  expect(releaseApi.list).toHaveBeenCalledTimes(3);
  expect(screen.queryByText("Something went off course")).not.toBeInTheDocument();
});
