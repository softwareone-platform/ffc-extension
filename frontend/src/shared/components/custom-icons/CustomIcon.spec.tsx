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

  beforeEach(() => {
    mockConsoleError = jest.spyOn(console, "error").mockImplementation(() => undefined);
  });

  afterEach(() => {
    mockConsoleError.mockRestore();
  });

  it("uses the default dimensions and static unknown icon when the name is empty", () => {
    const { asFragment } = render(<CustomIcon name="" />);

    expect(asFragment()).toMatchInlineSnapshot(`
      <DocumentFragment>
        <svg
          class=""
          height="24"
          viewBox="0 0 24 24"
          width="24"
          xmlns="http://www.w3.org/2000/svg"
        >
          <g
            data-testid="unknown-imported-icon"
          />
        </svg>
      </DocumentFragment>
    `);
  });

  it("uses explicit width and height when size is not provided", () => {
    const { asFragment } = render(
      <CustomIcon name="" width={16} height={18} boxWidth={30} boxHeight={32} className="x" />,
    );

    expect(asFragment()).toMatchInlineSnapshot(`
      <DocumentFragment>
        <svg
          class="x"
          height="18"
          viewBox="0 0 30 32"
          width="16"
          xmlns="http://www.w3.org/2000/svg"
        >
          <g
            data-testid="unknown-imported-icon"
          />
        </svg>
      </DocumentFragment>
    `);
  });

  it("overrides width and height with size when size is provided", () => {
    const { asFragment } = render(<CustomIcon name="" width={16} height={18} size={40} />);

    expect(asFragment()).toMatchInlineSnapshot(`
      <DocumentFragment>
        <svg
          class=""
          height="40"
          viewBox="0 0 24 24"
          width="40"
          xmlns="http://www.w3.org/2000/svg"
        >
          <g
            data-testid="unknown-imported-icon"
          />
        </svg>
      </DocumentFragment>
    `);
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
