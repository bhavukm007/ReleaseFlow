import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, expect, it, vi } from "vitest";
import { useAuth } from "../contexts/AuthContext";
import { AuthPage } from "./AuthPage";

vi.mock("../contexts/AuthContext", () => ({ useAuth: vi.fn() }));
const login = vi.fn().mockResolvedValue(undefined);

beforeEach(() => {
  login.mockClear();
  vi.mocked(useAuth).mockReturnValue({
    user: null, loading: false, startingServer: false, startupError: false, login, signup: vi.fn(), logout: vi.fn(),
  });
});

it("logs in and returns the user to the protected destination", async () => {
  const user = userEvent.setup();
  render(<MemoryRouter initialEntries={[{ pathname: "/login", state: { from: { pathname: "/teams" } } }]}>
    <Routes>
      <Route path="/login" element={<AuthPage mode="login" />} />
      <Route path="/teams" element={<p>Teams destination</p>} />
    </Routes>
  </MemoryRouter>);
  await user.type(screen.getByLabelText("Email"), "alice@example.com");
  await user.type(screen.getByLabelText("Password"), "safe-password");
  await user.click(screen.getByRole("button", { name: "Sign in" }));
  await waitFor(() => expect(login).toHaveBeenCalledWith("alice@example.com", "safe-password"));
  expect(screen.getByText("Teams destination")).toBeInTheDocument();
});

it("shows the forgot-password placeholder without submitting", async () => {
  await userEvent.setup().click(render(
    <MemoryRouter><AuthPage mode="login" /></MemoryRouter>,
  ).getByRole("button", { name: "Forgot password?" }));
  expect(screen.getByRole("alert")).toHaveTextContent("Password reset is coming soon");
  expect(login).not.toHaveBeenCalled();
});
