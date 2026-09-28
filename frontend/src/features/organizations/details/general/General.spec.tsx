import { screen, within } from "@testing-library/react";

import type { OrganizationRead } from "~api/ffc-api-model";
import type { useOrganizationDetailsApi } from "~organizations/api";
import { renderWithRouter } from "~test-utils";
import { mockDesignSystemText } from "~test-utils/mocks/designSystemText";
import { mockDesignSystemUtils } from "~test-utils/mocks/designSystemUtils";
import { mockDesignSystemInPageHighlight } from "~test-utils/mocks/inPageHighlight";

import { OrganizationGeneralDetails } from "./General";

type ApiResult = ReturnType<typeof useOrganizationDetailsApi>;

const mockUseOrganizationDetailsApi = jest.fn() as jest.MockedFunction<
  typeof useOrganizationDetailsApi
>;

jest.mock("~organizations/api", () => ({
  useOrganizationDetailsApi: (id: string | undefined) => mockUseOrganizationDetailsApi(id),
}));

jest.mock("@swo/design-system/in-page-highlight", () => mockDesignSystemInPageHighlight);

jest.mock("@swo/design-system/text", () => mockDesignSystemText);

jest.mock("@swo/design-system/utils", () => mockDesignSystemUtils);

function primeEntity(entity: Partial<OrganizationRead> | undefined) {
  mockUseOrganizationDetailsApi.mockReturnValue({ data: entity } as unknown as ApiResult);
}

function renderGeneral(url = "/organizations/org-1") {
  return renderWithRouter(<OrganizationGeneralDetails />, {
    initialUrl: url,
    routePath: "/organizations/:organizationId",
  });
}

describe("OrganizationGeneralDetails", () => {
  it("queries organization details using the organizationId route param", () => {
    primeEntity(undefined);

    renderGeneral();

    expect(mockUseOrganizationDetailsApi).toHaveBeenCalledWith("org-1");
  });

  it("renders four highlight items in fixed order", () => {
    primeEntity({ id: "org-1" });

    renderGeneral();

    const titles = screen.getAllByTestId("highlight-title").map((el) => el.textContent);
    expect(titles).toEqual([
      "operations_external_id",
      "linked_organization_id",
      "currency",
      "billing_currency",
    ]);
  });

  it("renders each highlight value pulled from the entity", () => {
    primeEntity({
      id: "org-1",
      operations_external_id: "ext-1",
      linked_organization_id: "linked-1",
      currency: "USD",
      billing_currency: "EUR",
    });

    renderGeneral();

    const items = screen.getAllByTestId("highlight-item");
    const values = items.map((item) => within(item).getByTestId("highlight-value").textContent);
    expect(values).toEqual(["ext-1", "linked-1", "USD", "EUR"]);
  });
});
