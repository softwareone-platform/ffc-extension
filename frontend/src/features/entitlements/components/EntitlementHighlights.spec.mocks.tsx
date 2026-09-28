import type { ComponentProps } from "react";

import type { useEntitlementsDetailsApi } from "~entitlements/api";
import { mockEntityReferenceCell } from "~test-utils/mocks/entityReferenceCell";
import { mockDesignSystemInPageHighlight } from "~test-utils/mocks/inPageHighlight";
import { mockCustomIcon } from "~test-utils/mocks/sharedGridCells";

import type { DataSourceEntityReference } from "./DataSourceEntityReference";

type MockNavigationHighlightsProps = ComponentProps<
  typeof import("@swo/design-system/navigation").Navigation.Highlights
>;
type MockDataSourceEntityReferenceProps = ComponentProps<typeof DataSourceEntityReference>;

export const mockUseEntitlementsDetailsApi = jest.fn() as jest.MockedFunction<
  typeof useEntitlementsDetailsApi
>;
export const mockDataSourceEntityReference = jest.fn() as jest.MockedFunction<
  (props: MockDataSourceEntityReferenceProps) => void
>;

jest.mock("~entitlements/api", () => ({
  useEntitlementsDetailsApi: (id: string | undefined) => mockUseEntitlementsDetailsApi(id),
}));

jest.mock("@swo/design-system/entity-reference-cell", () => mockEntityReferenceCell);
jest.mock("~shared/components/custom-icons/CustomIcon", () => mockCustomIcon);

jest.mock("./DataSourceEntityReference", () => ({
  DataSourceEntityReference: (props: MockDataSourceEntityReferenceProps) => {
    mockDataSourceEntityReference(props);
    return <div data-testid="datasource-entity-reference" />;
  },
}));

jest.mock("@swo/design-system/navigation", () => ({
  Navigation: {
    Highlights: ({ children }: MockNavigationHighlightsProps) => (
      <div data-testid="highlights-root">{children}</div>
    ),
  },
}));

jest.mock("@swo/design-system/in-page-highlight", () => mockDesignSystemInPageHighlight);

jest.mock("@swo/design-system/skeleton", () => ({
  Skeleton: () => <div data-testid="skeleton" />,
}));


