import type { ReactNode } from "react";

import { render, screen } from "@testing-library/react";

import { InlineErrorNotification } from "./InlineErrorNotification";

jest.mock("@swo/design-system/notification", () => ({
  InlineNotification: ({ children, status }: { children?: ReactNode; status: string }) => (
    <div data-testid="inline-notification" data-status={status}>
      {children}
    </div>
  ),
}));

describe("InlineErrorNotification", () => {
  it("renders nothing when the error is missing", () => {
    const { container } = render(<InlineErrorNotification error={null} />);

    expect(container).toBeEmptyDOMElement();
  });

  it("renders the error lines inside an error notification", () => {
    render(<InlineErrorNotification error={"First line\nSecond line"} />);

    expect(screen.getByTestId("inline-notification")).toHaveAttribute("data-status", "error");
    expect(screen.getByText("First line")).toHaveTextContent("First line");
    expect(screen.getByText("Second line")).toHaveTextContent("Second line");
    expect(screen.getByText("First line")).toContainHTML("<strong>First line</strong>");
  });
});
