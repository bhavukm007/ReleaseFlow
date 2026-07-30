import { render, screen } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, expect, it, vi } from "vitest";
import { useAuth } from "../contexts/AuthContext";
import { ProtectedRoute } from "./ProtectedRoute";

vi.mock("../contexts/AuthContext", () => ({ useAuth: vi.fn() }));

beforeEach(() => vi.mocked(useAuth).mockReturnValue({
  user: null,
  loading: false,
  startingServer: false,
  startupError: false,
  login: vi.fn(),
  signup: vi.fn(),
  logout: vi.fn(),
}));

it("redirects unauthenticated visitors to login", () => {
  render(<MemoryRouter initialEntries={["/private"]}><Routes>
    <Route element={<ProtectedRoute />}><Route path="/private" element={<p>Private workspace</p>} /></Route>
    <Route path="/login" element={<p>Login screen</p>} />
  </Routes></MemoryRouter>);
  expect(screen.getByText("Login screen")).toBeInTheDocument();
  expect(screen.queryByText("Private workspace")).not.toBeInTheDocument();
});

it("renders protected content for an authenticated user", () => {
  vi.mocked(useAuth).mockReturnValue({
    user: { id: "u1", full_name: "Alice", email: "alice@example.com", created_at: "", last_login: null },
    loading: false,
    startingServer: false,
    startupError: false,
    login: vi.fn(),
    signup: vi.fn(),
    logout: vi.fn(),
  });
  render(<MemoryRouter initialEntries={["/private"]}><Routes>
    <Route element={<ProtectedRoute />}><Route path="/private" element={<p>Private workspace</p>} /></Route>
  </Routes></MemoryRouter>);
  expect(screen.getByText("Private workspace")).toBeInTheDocument();
});
