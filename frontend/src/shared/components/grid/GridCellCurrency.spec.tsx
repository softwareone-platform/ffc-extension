import type { ComponentProps, PropsWithChildren } from "react";

import { render, screen } from "@testing-library/react";

import type { GridCellTitleSubtitle } from "@swo/design-system/grid";

import { useFormatMoney } from "~shared/utils/NumberUtils";
import { mockDesignSystemUtils } from "~test-utils/mocks/designSystemUtils";

import { GridCellCurrency } from "./GridCellCurrency";

type TitleSubtitleProps = Pick<ComponentProps<typeof GridCellTitleSubtitle>, "title" | "subtitle">;

const mockUseFormatMoney = jest.mocked(useFormatMoney);
const mockGridCellTitleSubtitle = jest.fn() as jest.MockedFunction<
  (props: TitleSubtitleProps) => void
>;

jest.mock("@swo/design-system/grid", () => ({
  GridCellSimple: ({ children }: PropsWithChildren) => (
    <div data-testid="grid-cell-simple">{children}</div>
  ),
  GridCellTitleSubtitle: ({ title, subtitle }: TitleSubtitleProps) => {
    mockGridCellTitleSubtitle({ title, subtitle });
    return (
      <div data-testid="grid-cell-title-subtitle">
        <div data-testid="title">{title}</div>
        <div data-testid="subtitle">{subtitle}</div>
      </div>
    );
  },
}));

jest.mock("@swo/design-system/utils", () => mockDesignSystemUtils);

jest.mock("~shared/utils/NumberUtils", () => ({
  useFormatMoney: jest.fn(),
}));

describe("GridCellCurrency", () => {
  beforeEach(() => {
    mockGridCellTitleSubtitle.mockReset();
    mockUseFormatMoney.mockReturnValue(
      (value?: number | null) => `formatted:${value ?? "missing"}`,
    );
  });

  it("renders a simple cell when no currency is provided", () => {
    render(<GridCellCurrency value={100} />);

    expect(mockUseFormatMoney).toHaveBeenCalledWith(undefined, false);
    expect(screen.getByTestId("grid-cell-simple")).toHaveTextContent("formatted:100");
    expect(screen.queryByTestId("grid-cell-title-subtitle")).not.toBeInTheDocument();
  });

  it("renders the title and subtitle cell when a currency is provided", () => {
    render(<GridCellCurrency value={100} currency="USD" />);

    expect(mockUseFormatMoney).toHaveBeenCalledWith("USD", false);
    expect(screen.getByTestId("title")).toHaveTextContent("formatted:100");
    expect(screen.getByTestId("subtitle")).toHaveTextContent("USD");
    expect(mockGridCellTitleSubtitle).toHaveBeenCalledTimes(1);
  });

  it("treats null currency like a missing currency", () => {
    render(<GridCellCurrency value={null} currency={null} />);

    expect(screen.getByTestId("grid-cell-simple")).toHaveTextContent("formatted:missing");
    expect(screen.queryByTestId("grid-cell-title-subtitle")).not.toBeInTheDocument();
  });
});
