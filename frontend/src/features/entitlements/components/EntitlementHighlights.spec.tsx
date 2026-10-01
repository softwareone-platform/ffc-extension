import { render, screen, within } from "@testing-library/react";

import type { useEntitlementsDetailsApi } from "~entitlements/api";
import { makeEntitlement } from "~test-utils";

import {
  mockDataSourceEntityReference,
  mockUseEntitlementsDetailsApi,
} from "./EntitlementHighlights.spec.mocks";

import type { Entitlement } from "../api/model";
import { EntitlementHighlights } from "./EntitlementHighlights";

type ApiResult = ReturnType<typeof useEntitlementsDetailsApi>;

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
    expect(screen.queryByTestId("in-page-highlight")).not.toBeInTheDocument();
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
