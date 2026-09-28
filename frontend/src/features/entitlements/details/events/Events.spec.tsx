import { screen } from "@testing-library/react";

import type { EntitlementRead } from "~api/ffc-api-model";
import type { useEntitlementsDetailsApi } from "~features/entitlements/api/useEntitlementsDetailsApi";
import type { EntityEvents } from "~shared/components/events/EntityEvents";
import { renderWithEntitlementRoute } from "~test-utils";

import { EntitlementEventsDetails } from "./Events";

type ApiResult = ReturnType<typeof useEntitlementsDetailsApi>;
type MockEntityEventsProps = Parameters<typeof EntityEvents<EntitlementRead>>[0];

const mockUseEntitlementsDetailsApi = jest.fn() as jest.MockedFunction<
  typeof useEntitlementsDetailsApi
>;
const mockEntityEvents = jest.fn() as jest.MockedFunction<(props: MockEntityEventsProps) => void>;

jest.mock("~features/entitlements/api/useEntitlementsDetailsApi", () => ({
  useEntitlementsDetailsApi: (id: string | undefined) => mockUseEntitlementsDetailsApi(id),
}));

jest.mock("~shared/components/events/EntityEvents", () => ({
  EntityEvents: (props: MockEntityEventsProps) => {
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

    renderWithEntitlementRoute(<EntitlementEventsDetails />);

    expect(mockUseEntitlementsDetailsApi).toHaveBeenCalledWith("ent-1");
  });

  it("renders EntityEvents with the loaded entity", () => {
    primeEntity({ id: "ent-1", name: "One" });

    renderWithEntitlementRoute(<EntitlementEventsDetails />);

    expect(screen.getByTestId("entity-events")).toHaveTextContent("ent-1");
  });

  it("renders nothing until the entity is loaded", () => {
    primeEntity(undefined);

    renderWithEntitlementRoute(<EntitlementEventsDetails />);

    expect(screen.queryByTestId("entity-events")).not.toBeInTheDocument();
  });
});
