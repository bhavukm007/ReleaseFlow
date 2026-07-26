import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { beforeEach, expect, it, vi } from "vitest";
import { releaseApi } from "../api/releases";
import { STEP_NAMES, type Release } from "../types";
import { ReleaseDetailsPage } from "./ReleaseDetailsPage";

vi.mock("../api/releases", () => ({
  releaseApi: {
    get: vi.fn(),
    updateSteps: vi.fn(),
    updateInfo: vi.fn(),
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
};

beforeEach(() => {
  vi.mocked(releaseApi.get).mockResolvedValue(plannedRelease);
  vi.mocked(releaseApi.updateSteps).mockImplementation(async (_id, steps) => ({
    ...plannedRelease,
    steps,
    status: "ongoing",
    completed_steps: 1,
  }));
});

it("updates a checklist step and refreshes status and progress immediately", async () => {
  const user = userEvent.setup();
  render(
    <MemoryRouter initialEntries={["/releases/7"]}>
      <Routes><Route path="/releases/:id" element={<ReleaseDetailsPage />} /></Routes>
    </MemoryRouter>,
  );

  expect(await screen.findByRole("heading", { name: "Production Launch" })).toBeInTheDocument();
  await user.click(screen.getByRole("checkbox", { name: "Code Freeze 01" }));

  expect(screen.getByText("ongoing")).toBeInTheDocument();
  expect(screen.getByText("1 / 8 Completed")).toBeInTheDocument();
  await waitFor(() => expect(releaseApi.updateSteps).toHaveBeenCalledTimes(1));
});
