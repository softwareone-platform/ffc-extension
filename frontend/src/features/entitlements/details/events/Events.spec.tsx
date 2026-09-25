import { screen } from "@testing-library/react";

import type { EntitlementRead } from "~api/ffc-api-model";
import type { useEntitlementsDetailsApi } from "~features/entitlements/api/useEntitlementsDetailsApi";
import { renderWithRouter } from "~test-utils";

import { EntitlementEventsDetails } from "./Events";

type ApiResult = ReturnType<typeof useEntitlementsDetailsApi>;

const mockUseEntitlementsDetailsApi = jest.fn() as jest.MockedFunction<
  typeof useEntitlementsDetailsApi
>;
const mockEntityEvents = jest.fn() as jest.MockedFunction<
  (props: { entity: EntitlementRead }) => void
>;

jest.mock("~features/entitlements/api/useEntitlementsDetailsApi", () => ({
  useEntitlementsDetailsApi: (id: string | undefined) => mockUseEntitlementsDetailsApi(id),
}));

jest.mock("~shared/components/events/EntityEvents", () => ({
  EntityEvents: (props: { entity: EntitlementRead }) => {
    mockEntityEvents(props);
    return <div data-testid="entity-events">{props.entity.id}</div>;
  },
}));

function primeEntity(entity: Partial<EntitlementRead> | undefined) {
  mockUseEntitlementsDetailsApi.mockReturnValue({ data: entity } as unknown as ApiResult);
}

describe("EntitlementEventsDetails", () => {
  it("queries entitlement details using the entitlementId route param", () => {
    primeEntity(undefined);

    renderWithRouter(<EntitlementEventsDetails />, {
      initialUrl: "/entitlements/ent-1",
      routePath: "/entitlements/:entitlementId",
    });

    expect(mockUseEntitlementsDetailsApi).toHaveBeenCalledWith("ent-1");
  });

  it("renders EntityEvents with the loaded entity", () => {
    primeEntity({ id: "ent-1", name: "One" });

    renderWithRouter(<EntitlementEventsDetails />, {
      initialUrl: "/entitlements/ent-1",
      routePath: "/entitlements/:entitlementId",
    });

    expect(screen.getByTestId("entity-events")).toHaveTextContent("ent-1");
  });

  it("renders nothing until the entity is loaded", () => {
    primeEntity(undefined);

    renderWithRouter(<EntitlementEventsDetails />, {
      initialUrl: "/entitlements/ent-1",
      routePath: "/entitlements/:entitlementId",
    });

    expect(screen.queryByTestId("entity-events")).not.toBeInTheDocument();
  });
});
