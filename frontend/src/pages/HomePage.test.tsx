import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { beforeEach, expect, it, vi } from "vitest";
import { releaseApi } from "../api/releases";
import { STEP_NAMES, type Release } from "../types";
import { HomePage } from "./HomePage";

vi.mock("../api/releases", () => ({
  releaseApi: {
    list: vi.fn(),
    create: vi.fn(),
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
};

beforeEach(() => {
  vi.mocked(releaseApi.list).mockResolvedValue([release]);
  vi.mocked(releaseApi.create).mockResolvedValue({ ...release, id: 2, name: "API Launch" });
});

it("loads releases and creates a new release through the modal", async () => {
  const user = userEvent.setup();
  render(<MemoryRouter><HomePage /></MemoryRouter>);

  expect(await screen.findByText("Web Launch")).toBeInTheDocument();
  await user.click(screen.getByRole("button", { name: "New release" }));
  await user.type(screen.getByLabelText("Release name"), "API Launch");
  await user.type(screen.getByLabelText("Due date"), "2026-08-21");
  await user.click(screen.getByRole("button", { name: "Create release" }));

  await waitFor(() => expect(releaseApi.create).toHaveBeenCalledWith({
    name: "API Launch",
    due_date: "2026-08-21",
    additional_info: null,
  }));
  expect(await screen.findByText("Release created")).toBeInTheDocument();
});
