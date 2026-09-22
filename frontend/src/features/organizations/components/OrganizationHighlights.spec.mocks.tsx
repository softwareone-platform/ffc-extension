import type { ComponentProps, ReactNode } from "react";

import type { useOrganizationDetailsApi } from "~organizations/api";
import type { useFormatMoney } from "~shared/utils/NumberUtils";

type MockInPageHighlightProps = ComponentProps<
  typeof import("@swo/design-system/in-page-highlight").InPageHighlight
>;
type MockInPageHighlightItemProps = ComponentProps<
  typeof import("@swo/design-system/in-page-highlight").InPageHighlight.Item
>;
type MockNavigationHighlightsProps = ComponentProps<
  typeof import("@swo/design-system/navigation").Navigation.Highlights
>;

export const mockUseOrganizationDetailsApi = jest.fn() as jest.MockedFunction<
  typeof useOrganizationDetailsApi
>;
export const mockUseFormatMoney = jest.fn() as jest.MockedFunction<typeof useFormatMoney>;

jest.mock("~organizations/api", () => ({
  useOrganizationDetailsApi: (id: string | undefined) => mockUseOrganizationDetailsApi(id),
}));

jest.mock("~shared/utils/NumberUtils", () => ({
  useFormatMoney: (...args: Parameters<typeof useFormatMoney>) => mockUseFormatMoney(...args),
}));

jest.mock("@swo/design-system/utils", () => ({
  DisplayValue: ({ value, transform }: { value: number; transform?: (v: number) => unknown }) => (
    <>{transform ? transform(value) : value}</>
  ),
}));

jest.mock("@swo/design-system/navigation", () => ({
  Navigation: {
    Highlights: ({ children }: MockNavigationHighlightsProps) => (
      <div data-testid="highlights-root">{children}</div>
    ),
  },
}));

jest.mock("@swo/design-system/in-page-highlight", () => {
  const InPageHighlight = ({ children }: MockInPageHighlightProps) => (
    <div data-testid="highlights">{children}</div>
  );
  InPageHighlight.Item = ({ children, title }: MockInPageHighlightItemProps) => (
    <div data-testid="highlight-item">
      <span data-testid="highlight-title">{title as ReactNode}</span>
      <span data-testid="highlight-value">{children}</span>
    </div>
  );
  return { InPageHighlight };
});

jest.mock("@swo/design-system/skeleton", () => ({
  Skeleton: () => <div data-testid="skeleton" />,
}));
