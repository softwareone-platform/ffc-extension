import { render, screen, waitFor } from "@testing-library/react";

import CustomIcon from "./CustomIcon";

jest.mock("./icons/unknown.tsx", () => ({
  __esModule: true,
  default: <g data-testid="unknown-imported-icon" />,
}));

jest.mock("./icons/aws.tsx", () => ({
  __esModule: true,
  default: <g data-testid="aws-icon" />,
}));

describe("CustomIcon", () => {
  let mockConsoleError: jest.SpiedFunction<typeof console.error>;

  function getRenderedSvg() {
    return (screen.getByTestId("unknown-imported-icon") as unknown as SVGGElement).ownerSVGElement;
  }

  beforeEach(() => {
    mockConsoleError = jest.spyOn(console, "error").mockImplementation(() => undefined);
  });

  afterEach(() => {
    mockConsoleError.mockRestore();
  });

  it("uses the default dimensions and static unknown icon when the name is empty", () => {
    render(<CustomIcon name="" />);

    expect(getRenderedSvg()).toHaveAttribute("width", "24");
    expect(getRenderedSvg()).toHaveAttribute("height", "24");
    expect(getRenderedSvg()).toHaveAttribute("viewBox", "0 0 24 24");
    expect(getRenderedSvg()).toHaveAttribute("class", "");
  });

  it("uses explicit width and height when size is not provided", () => {
    render(
      <CustomIcon name="" width={16} height={18} boxWidth={30} boxHeight={32} className="x" />,
    );

    expect(getRenderedSvg()).toHaveAttribute("width", "16");
    expect(getRenderedSvg()).toHaveAttribute("height", "18");
    expect(getRenderedSvg()).toHaveAttribute("viewBox", "0 0 30 32");
    expect(getRenderedSvg()).toHaveClass("x");
  });

  it("overrides width and height with size when size is provided", () => {
    render(<CustomIcon name="" width={16} height={18} size={40} />);

    expect(getRenderedSvg()).toHaveAttribute("width", "40");
    expect(getRenderedSvg()).toHaveAttribute("height", "40");
    expect(getRenderedSvg()).toHaveAttribute("viewBox", "0 0 24 24");
  });

  it("renders the static unknown icon before asynchronously loading a supported icon", async () => {
    render(<CustomIcon name="aws" />);

    expect(screen.getByTestId("unknown-imported-icon")).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByTestId("aws-icon")).toBeInTheDocument();
    });
  });

  it("falls back to the imported unknown icon when the icon name is unsupported", async () => {
    render(<CustomIcon name="not-supported" />);

    await waitFor(() => {
      expect(screen.getByTestId("unknown-imported-icon")).toBeInTheDocument();
    });
  });
});
