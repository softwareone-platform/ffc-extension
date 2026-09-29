import { screen, within } from "@testing-library/react";

import type { EntitlementRead } from "~api/ffc-api-model";
import type { useEntitlementsDetailsApi } from "~entitlements/api";
import { renderWithEntitlementRoute } from "~test-utils";
import { mockDesignSystemText } from "~test-utils/mocks/designSystemText";
import { mockDesignSystemUtils } from "~test-utils/mocks/designSystemUtils";
import { mockDesignSystemInPageHighlight } from "~test-utils/mocks/inPageHighlight";

import { EntitlementsGeneralDetails } from "./General";

type ApiResult = ReturnType<typeof useEntitlementsDetailsApi>;

const mockUseEntitlementsDetailsApi = jest.fn() as jest.MockedFunction<
  typeof useEntitlementsDetailsApi
>;

jest.mock("~entitlements/api", () => ({
  useEntitlementsDetailsApi: (id: string | undefined) => mockUseEntitlementsDetailsApi(id),
}));

jest.mock("@swo/design-system/in-page-highlight", () => mockDesignSystemInPageHighlight);

jest.mock("@swo/design-system/text", () => mockDesignSystemText);

jest.mock("@swo/design-system/utils", () => mockDesignSystemUtils);

function primeEntity(entity: Partial<EntitlementRead> | undefined) {
  mockUseEntitlementsDetailsApi.mockReturnValue({ data: entity } as unknown as ApiResult);
}

describe("EntitlementsGeneralDetails", () => {
  it("queries entitlement details using the entitlementId route param", () => {
    primeEntity(undefined);

    renderWithEntitlementRoute(<EntitlementsGeneralDetails />);

    expect(mockUseEntitlementsDetailsApi).toHaveBeenCalledWith("ent-1");
  });

  it("renders linkedDataSource and affiliate_external_id highlights in order", () => {
    primeEntity({ id: "ent-1" });

    renderWithEntitlementRoute(<EntitlementsGeneralDetails />);

    const titles = screen.getAllByTestId("highlight-title").map((el) => el.textContent);
    expect(titles).toEqual(["linkedDataSource", "affiliate_external_id"]);
  });

  it("renders the entity fields via DisplayValue when present", () => {
    primeEntity({
      id: "ent-1",
      linked_datasource_id: "linked-ds-1",
      affiliate_external_id: "aff-ext-1",
    });

    renderWithEntitlementRoute(<EntitlementsGeneralDetails />);

    const items = screen.getAllByTestId("highlight-item");
    expect(within(items[0]).getByTestId("highlight-value")).toHaveTextContent("linked-ds-1");
    expect(within(items[1]).getByTestId("highlight-value")).toHaveTextContent("aff-ext-1");
  });

  it("falls back to NO_VALUE for missing fields", () => {
    primeEntity({ id: "ent-1" });

    renderWithEntitlementRoute(<EntitlementsGeneralDetails />);

    const values = screen.getAllByTestId("highlight-value").map((el) => el.textContent);
    expect(values).toEqual(["—", "—"]);
  });
});
