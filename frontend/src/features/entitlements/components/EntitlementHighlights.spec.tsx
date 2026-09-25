import type { ComponentProps, ReactNode } from "react";

import { render, screen, within } from "@testing-library/react";

import type { useEntitlementsDetailsApi } from "~entitlements/api";
import { makeEntitlement } from "~test-utils";
import { mockEntityReferenceCell } from "~test-utils/mocks/entityReferenceCell";
import { mockCustomIcon } from "~test-utils/mocks/sharedGridCells";

import type { Entitlement } from "../api/model";
import type { DataSourceEntityReference } from "./DataSourceEntityReference";
import { EntitlementHighlights } from "./EntitlementHighlights";

type ApiResult = ReturnType<typeof useEntitlementsDetailsApi>;
type MockInPageHighlightProps = ComponentProps<
  typeof import("@swo/design-system/in-page-highlight").InPageHighlight
>;
type MockInPageHighlightItemProps = ComponentProps<
  typeof import("@swo/design-system/in-page-highlight").InPageHighlight.Item
>;
type MockNavigationHighlightsProps = ComponentProps<
  typeof import("@swo/design-system/navigation").Navigation.Highlights
>;
type MockDataSourceEntityReferenceProps = ComponentProps<typeof DataSourceEntityReference>;

const mockUseEntitlementsDetailsApi = jest.fn() as jest.MockedFunction<
  typeof useEntitlementsDetailsApi
>;
const mockDataSourceEntityReference = jest.fn() as jest.MockedFunction<
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

function primeEntity(entity: Partial<Entitlement> | undefined) {
  mockUseEntitlementsDetailsApi.mockReturnValue({ data: entity } as unknown as ApiResult);
}

describe("EntitlementHighlights", () => {
  it("queries entitlement details for the supplied entitlementId", () => {
    primeEntity(undefined);

    render(<EntitlementHighlights entitlementId="ent-1" />);

    expect(mockUseEntitlementsDetailsApi).toHaveBeenCalledWith("ent-1");
  });

  it("renders a Skeleton while the entity is not loaded", () => {
    primeEntity(undefined);

    render(<EntitlementHighlights entitlementId="ent-1" />);

    expect(screen.getByTestId("skeleton")).toBeInTheDocument();
    expect(screen.queryByTestId("highlights")).not.toBeInTheDocument();
  });

  it("renders three highlight items in fixed order when the entity has an id", () => {
    primeEntity(makeEntitlement({ id: "ent-1" }));

    render(<EntitlementHighlights entitlementId="ent-1" />);

    const titles = screen.getAllByTestId("highlight-title").map((el) => el.textContent);
    expect(titles).toEqual(["affiliate_external_id", "data_source", "organization"]);
  });

  it("renders the owner name and id, and passes owner.integration to CustomIcon", () => {
    primeEntity(
      makeEntitlement({
        id: "ent-1",
        owner: {
          id: "own-1",
          external_id: "own-ext-1",
          name: "Owner Name",
          type: "affiliate",
          integration: "microsoft",
        },
      }),
    );

    render(<EntitlementHighlights entitlementId="ent-1" />);

    const affiliateItem = screen.getAllByTestId("highlight-item")[0];
    expect(within(affiliateItem).getByTestId("primary")).toHaveTextContent("Owner Name");
    expect(within(affiliateItem).getByTestId("secondary")).toHaveTextContent("own-1");
    expect(within(affiliateItem).getByTestId("custom-icon")).toHaveTextContent("microsoft");
  });

  it("delegates the data_source highlight to DataSourceEntityReference with the entity", () => {
    const entity = makeEntitlement({ id: "ent-1" });
    primeEntity(entity);

    render(<EntitlementHighlights entitlementId="ent-1" />);

    expect(mockDataSourceEntityReference).toHaveBeenCalledWith({ entity });
  });

  it("renders NO_VALUE for organization when the entitlement has not been redeemed", () => {
    primeEntity(
      makeEntitlement({
        id: "ent-1",
        events: { redeemed: null } as unknown as Entitlement["events"],
      }),
    );

    render(<EntitlementHighlights entitlementId="ent-1" />);

    const organizationItem = screen.getAllByTestId("highlight-item")[2];
    expect(within(organizationItem).getByTestId("highlight-value")).toHaveTextContent("—");
  });

  it("renders the redeeming organization name and id when redeemed", () => {
    primeEntity(
      makeEntitlement({
        id: "ent-1",
        events: {
          redeemed: {
            by: { id: "org-1", name: "Redeeming Org" },
          },
        } as unknown as Entitlement["events"],
      }),
    );

    render(<EntitlementHighlights entitlementId="ent-1" />);

    const organizationItem = screen.getAllByTestId("highlight-item")[2];
    expect(within(organizationItem).getByTestId("primary")).toHaveTextContent("Redeeming Org");
    expect(within(organizationItem).getByTestId("secondary")).toHaveTextContent("org-1");
  });
});
