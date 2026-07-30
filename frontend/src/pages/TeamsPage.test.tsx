import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, expect, it, vi } from "vitest";
import { teamApi } from "../api/teams";
import { useAuth } from "../contexts/AuthContext";
import type { Team } from "../types";
import { TeamsPage } from "./TeamsPage";

vi.mock("../api/teams", () => ({ teamApi: {
  list: vi.fn(), create: vi.fn(), invite: vi.fn(), remove: vi.fn(), transfer: vi.fn(), delete: vi.fn(),
} }));
vi.mock("../contexts/AuthContext", () => ({ useAuth: vi.fn() }));

const team: Team = {
  id: "team-1", name: "Platform", owner_id: "user-1", role: "owner", created_at: "",
  members: [{ user_id: "user-1", full_name: "Alice Owner", email: "alice@example.com", role: "owner" }],
  invitations: [{ id: "invite-1", email: "pending@example.com", role: "member", created_at: "" }],
};

beforeEach(() => {
  vi.mocked(teamApi.list).mockResolvedValue([team]);
  vi.mocked(teamApi.invite).mockResolvedValue({ status: "invitation_pending" });
  vi.mocked(useAuth).mockReturnValue({
    user: { id: "user-1", full_name: "Alice Owner", email: "alice@example.com", created_at: "", last_login: null },
    loading: false, startingServer: false, startupError: false, login: vi.fn(), signup: vi.fn(), logout: vi.fn(),
  });
});

it("shows team roles and sends an invitation", async () => {
  const user = userEvent.setup();
  render(<QueryClientProvider client={new QueryClient({ defaultOptions: { queries: { retry: false } } })}>
    <TeamsPage />
  </QueryClientProvider>);
  expect(await screen.findByRole("heading", { name: "Platform" })).toBeInTheDocument();
  expect(screen.getByText("pending@example.com")).toBeInTheDocument();
  await user.type(screen.getByLabelText("Invite email"), "new@example.com");
  await user.click(screen.getByRole("button", { name: "Invite" }));
  await waitFor(() => expect(teamApi.invite).toHaveBeenCalledWith("team-1", "new@example.com", "member"));
  expect(screen.getByRole("status")).toHaveTextContent("Invitation will be applied");
});
