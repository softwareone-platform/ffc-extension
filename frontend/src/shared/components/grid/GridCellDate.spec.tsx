import type { ComponentProps } from "react";

import { render, screen } from "@testing-library/react";

import type { GridCellTitleSubtitle } from "@swo/design-system/grid";
import type { DisplayValue } from "@swo/design-system/utils";
import { useFormatDate } from "@swo/design-system/utils";

import { useFormatTime } from "~shared/hooks/useFormatTime";

import { GridCellDate } from "./GridCellDate";

type TitleSubtitleProps = Pick<ComponentProps<typeof GridCellTitleSubtitle>, "title" | "subtitle">;
type DisplayValueProps = Pick<ComponentProps<typeof DisplayValue>, "value" | "transform">;

const mockGridCellTitleSubtitle = jest.fn() as jest.MockedFunction<
  (props: TitleSubtitleProps) => void
>;
const mockUseFormatDate = jest.mocked(useFormatDate);
const mockUseFormatTime = jest.mocked(useFormatTime);

jest.mock("@swo/design-system/grid", () => ({
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

jest.mock("@swo/design-system/utils", () => ({
  DisplayValue: ({ value, transform }: DisplayValueProps) => (
    <>{transform ? transform(value) : (value ?? "—")}</>
  ),
  useFormatDate: jest.fn(),
}));

jest.mock("~shared/hooks/useFormatTime", () => ({
  useFormatTime: jest.fn(),
}));

describe("GridCellDate", () => {
  beforeEach(() => {
    mockGridCellTitleSubtitle.mockReset();
    mockUseFormatDate.mockReturnValue((value) => `date:${String(value)}`);
    mockUseFormatTime.mockReturnValue((value) => `time:${String(value)}`);
  });

  it("renders formatted date and time for a string value", () => {
    render(<GridCellDate value="2026-01-02T10:20:30Z" />);

    expect(screen.getByTestId("title")).toHaveTextContent("date:2026-01-02T10:20:30Z");
    expect(screen.getByTestId("subtitle")).toHaveTextContent("time:2026-01-02T10:20:30Z");
    expect(mockGridCellTitleSubtitle).toHaveBeenCalledTimes(1);
  });

  it("renders formatted date and time for a Date value", () => {
    const value = new Date("2026-01-02T10:20:30Z");

    render(<GridCellDate value={value} />);

    expect(screen.getByTestId("title")).toHaveTextContent(`date:${String(value)}`);
    expect(screen.getByTestId("subtitle")).toHaveTextContent(`time:${String(value)}`);
  });

  it("passes missing values through both display lines", () => {
    render(<GridCellDate value={null} />);

    expect(screen.getByTestId("title")).toHaveTextContent("date:null");
    expect(screen.getByTestId("subtitle")).toHaveTextContent("time:null");
  });
});
