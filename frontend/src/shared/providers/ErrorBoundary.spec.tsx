import type { ReactElement } from "react";

import { render, screen } from "@testing-library/react";

import { ErrorBoundary } from "./ErrorBoundary";

const mockOnError = jest.fn();

function ExplodingChild(): ReactElement {
  throw new Error("boom");
}

describe("ErrorBoundary", () => {
  let mockConsoleError: jest.SpiedFunction<typeof console.error>;

  beforeEach(() => {
    mockOnError.mockReset();
    mockConsoleError = jest.spyOn(console, "error").mockImplementation(() => undefined);
  });

  afterEach(() => {
    mockConsoleError.mockRestore();
  });

  it("renders children when no descendant throws", () => {
    render(
      <ErrorBoundary fallback={<div>fallback</div>} onError={mockOnError}>
        <div>child</div>
      </ErrorBoundary>,
    );

    expect(screen.getByText("child")).toBeInTheDocument();
    expect(screen.queryByText("fallback")).not.toBeInTheDocument();
    expect(mockOnError).not.toHaveBeenCalled();
  });

  it("renders the fallback and reports the error when a descendant throws", () => {
    render(
      <ErrorBoundary fallback={<div>fallback</div>} onError={mockOnError}>
        <ExplodingChild />
      </ErrorBoundary>,
    );

    expect(screen.getByText("fallback")).toBeInTheDocument();
    expect(mockOnError).toHaveBeenCalledWith(
      expect.objectContaining({ message: "boom" }),
      expect.objectContaining({ componentStack: expect.any(String) }),
    );
  });

  it("renders an empty fallback when no fallback prop is provided", () => {
    render(
      <ErrorBoundary onError={mockOnError}>
        <ExplodingChild />
      </ErrorBoundary>,
    );

    expect(screen.queryByText("fallback")).not.toBeInTheDocument();
    expect(mockOnError).toHaveBeenCalledWith(
      expect.objectContaining({ message: "boom" }),
      expect.objectContaining({ componentStack: expect.any(String) }),
    );
  });
});
