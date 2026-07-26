import { render, screen } from "@testing-library/react";
import { StatusBadge } from "./StatusBadge";

it("renders the computed status", () => {
  render(<StatusBadge status="ongoing" />);
  expect(screen.getByText("ongoing")).toBeInTheDocument();
});
