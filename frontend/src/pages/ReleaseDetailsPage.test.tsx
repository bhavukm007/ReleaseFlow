import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { beforeEach, expect, it, vi } from "vitest";
import { releaseApi } from "../api/releases";
import { STEP_NAMES, type Release } from "../types";
import { ReleaseDetailsPage } from "./ReleaseDetailsPage";

vi.mock("../api/teams", () => ({ teamApi: { list: vi.fn().mockResolvedValue([]) } }));
vi.mock("../contexts/AuthContext", () => ({ useAuth: () => ({
  user: { id: "00000000-0000-0000-0000-000000000001", full_name: "Test User", email: "test@example.com" },
}) }));

vi.mock("../api/releases", () => ({
  releaseApi: {
    get: vi.fn(),
    updateSteps: vi.fn(),
    update: vi.fn(),
    updateChecklist: vi.fn(),
    updateInfo: vi.fn(),
    activities: vi.fn(),
    addCollaborator: vi.fn(),
    updateCollaborator: vi.fn(),
    removeCollaborator: vi.fn(),
    delete: vi.fn(),
  },
}));

const plannedRelease: Release = {
  id: 7,
  name: "Production Launch",
  due_date: "2026-08-20",
  additional_info: "Initial notes",
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
  vi.mocked(releaseApi.get).mockResolvedValue(plannedRelease);
  vi.mocked(releaseApi.updateChecklist).mockImplementation(async (_id, steps) => ({
    ...plannedRelease,
    steps,
    status: "ongoing",
    completed_steps: 1,
  }));
  vi.mocked(releaseApi.activities).mockResolvedValue([{
    id: "activity-1", release_id: 7, team_id: null, user_id: "user-1",
    user_name: "Alice", action: "checklist_completed", metadata: { step: "QA Completed" },
    created_at: "2026-07-26T10:25:00Z",
  }]);
  vi.mocked(releaseApi.addCollaborator).mockResolvedValue({
    ...plannedRelease,
    collaborators: [...plannedRelease.collaborators, {
      user_id: "user-2", full_name: "Admin User", email: "admin@example.com", role: "admin",
    }],
  });
});

it("renders legacy release responses that do not include collaborators", async () => {
  const legacyRelease = { ...plannedRelease } as Partial<Release>;
  delete legacyRelease.collaborators;
  vi.mocked(releaseApi.get).mockResolvedValue(legacyRelease as Release);
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });

  render(
    <QueryClientProvider client={queryClient}><MemoryRouter initialEntries={["/releases/7"]}>
      <Routes><Route path="/releases/:id" element={<ReleaseDetailsPage />} /></Routes>
    </MemoryRouter></QueryClientProvider>,
  );

  expect(await screen.findByRole("heading", { name: "Production Launch" })).toBeInTheDocument();
  expect(screen.getByRole("heading", { name: "Teammates" })).toBeInTheDocument();
});

it("updates a checklist step and refreshes status and progress immediately", async () => {
  const user = userEvent.setup();
  const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <QueryClientProvider client={queryClient}><MemoryRouter initialEntries={["/releases/7"]}>
      <Routes><Route path="/releases/:id" element={<ReleaseDetailsPage />} /></Routes>
    </MemoryRouter></QueryClientProvider>,
  );

  expect(await screen.findByRole("heading", { name: "Production Launch" })).toBeInTheDocument();
  expect(await screen.findByText("Alice")).toBeInTheDocument();
  expect(screen.getByText("QA Completed", { selector: "q" })).toBeInTheDocument();
  await user.click(screen.getByRole("checkbox", { name: "Code Freeze" }));

  await waitFor(() => expect(screen.getByText("ongoing")).toBeInTheDocument());
  expect(screen.getByText("1 / 8 Completed")).toBeInTheDocument();
  await waitFor(() => expect(releaseApi.updateChecklist).toHaveBeenCalledTimes(1));
  await user.type(screen.getByLabelText("Release teammate email"), "admin@example.com");
  await user.selectOptions(screen.getByLabelText("Release teammate role"), "admin");
  await user.click(screen.getByRole("button", { name: "Add" }));
  await waitFor(() => expect(releaseApi.addCollaborator).toHaveBeenCalledWith(7, {
    email: "admin@example.com", role: "admin",
  }));
  expect(await screen.findByText("Admin User")).toBeInTheDocument();
});
