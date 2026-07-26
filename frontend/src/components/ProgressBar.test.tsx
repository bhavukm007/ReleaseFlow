import { render, screen } from "@testing-library/react";
import { ProgressBar } from "./ProgressBar";

it("renders completed count and accessible percentage", () => {
  render(<ProgressBar completed={3} total={8} />);
  expect(screen.getByText("3 / 8 Completed")).toBeInTheDocument();
  expect(screen.getByRole("progressbar")).toHaveAttribute("aria-valuenow", "38");
});
