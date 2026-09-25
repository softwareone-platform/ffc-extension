import type { ComponentProps, ReactNode } from "react";

import { screen, within } from "@testing-library/react";

import type { EntitlementRead } from "~api/ffc-api-model";
import type { useEntitlementsDetailsApi } from "~entitlements/api";
import { renderWithRouter } from "~test-utils";

import { EntitlementsGeneralDetails } from "./General";

type ApiResult = ReturnType<typeof useEntitlementsDetailsApi>;
type MockInPageHighlightProps = ComponentProps<
  typeof import("@swo/design-system/in-page-highlight").InPageHighlight
>;
type MockInPageHighlightItemProps = ComponentProps<
  typeof import("@swo/design-system/in-page-highlight").InPageHighlight.Item
>;

const mockUseEntitlementsDetailsApi = jest.fn() as jest.MockedFunction<
  typeof useEntitlementsDetailsApi
>;

jest.mock("~entitlements/api", () => ({
  useEntitlementsDetailsApi: (id: string | undefined) => mockUseEntitlementsDetailsApi(id),
}));

jest.mock("@swo/design-system/in-page-highlight", () => {
  const InPageHighlight = ({ children }: MockInPageHighlightProps) => (
    <div data-testid="in-page-highlight">{children}</div>
  );
  InPageHighlight.Item = ({ children, title }: MockInPageHighlightItemProps) => (
    <div data-testid="highlight-item">
      <span data-testid="highlight-title">{title as ReactNode}</span>
      <span data-testid="highlight-value">{children}</span>
    </div>
  );
  return { InPageHighlight };
});

jest.mock("@swo/design-system/text", () => ({
  BoldText: ({ children }: { children?: ReactNode }) => <>{children}</>,
  MediumText: ({ children }: { children?: ReactNode }) => <span>{children}</span>,
}));

jest.mock("@swo/design-system/utils", () => ({
  NO_VALUE: "—",
  DisplayValue: ({ value }: { value?: unknown }) => <>{value ?? ""}</>,
}));

function primeEntity(entity: Partial<EntitlementRead> | undefined) {
  mockUseEntitlementsDetailsApi.mockReturnValue({ data: entity } as unknown as ApiResult);
}

function renderGeneral(url = "/entitlements/ent-1") {
  return renderWithRouter(<EntitlementsGeneralDetails />, {
    initialUrl: url,
    routePath: "/entitlements/:entitlementId",
  });
}

describe("EntitlementsGeneralDetails", () => {
  it("queries entitlement details using the entitlementId route param", () => {
    primeEntity(undefined);

    renderGeneral();

    expect(mockUseEntitlementsDetailsApi).toHaveBeenCalledWith("ent-1");
  });

  it("renders linkedDataSource and affiliate_external_id highlights in order", () => {
    primeEntity({ id: "ent-1" });

    renderGeneral();

    const titles = screen.getAllByTestId("highlight-title").map((el) => el.textContent);
    expect(titles).toEqual(["linkedDataSource", "affiliate_external_id"]);
  });

  it("renders the entity fields via DisplayValue when present", () => {
    primeEntity({
      id: "ent-1",
      linked_datasource_id: "linked-ds-1",
      affiliate_external_id: "aff-ext-1",
    });

    renderGeneral();

    const items = screen.getAllByTestId("highlight-item");
    expect(within(items[0]).getByTestId("highlight-value")).toHaveTextContent("linked-ds-1");
    expect(within(items[1]).getByTestId("highlight-value")).toHaveTextContent("aff-ext-1");
  });

  it("falls back to NO_VALUE for missing fields", () => {
    primeEntity({ id: "ent-1" });

    renderGeneral();

    const values = screen.getAllByTestId("highlight-value").map((el) => el.textContent);
    expect(values).toEqual(["—", "—"]);
  });
});
