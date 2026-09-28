import { screen } from "@testing-library/react";

import type { OrganizationRead } from "~api/ffc-api-model";
import type { useOrganizationDetailsApi } from "~features/organizations/api/useOrganizationDetailsApi";
import { renderWithOrganizationRoute } from "~test-utils";

import { OrganizationEventsDetails } from "./Events";

type ApiResult = ReturnType<typeof useOrganizationDetailsApi>;

const mockUseOrganizationDetailsApi = jest.fn() as jest.MockedFunction<
  typeof useOrganizationDetailsApi
>;
const mockEntityEvents = jest.fn() as jest.MockedFunction<
  (props: { entity: OrganizationRead }) => void
>;

jest.mock("~features/organizations/api/useOrganizationDetailsApi", () => ({
  useOrganizationDetailsApi: (id: string | undefined) => mockUseOrganizationDetailsApi(id),
}));

jest.mock("~shared/components/events/EntityEvents", () => ({
  EntityEvents: (props: { entity: OrganizationRead }) => {
    mockEntityEvents(props);
    return <div data-testid="entity-events">{props.entity.id}</div>;
  },
}));

function primeEntity(entity: Partial<OrganizationRead> | undefined) {
  mockUseOrganizationDetailsApi.mockReturnValue({ data: entity } as unknown as ApiResult);
}

describe("OrganizationEventsDetails", () => {
  it("queries organization details using the organizationId route param", () => {
    primeEntity(undefined);

    renderWithOrganizationRoute(<OrganizationEventsDetails />);

    expect(mockUseOrganizationDetailsApi).toHaveBeenCalledWith("org-1");
  });

  it("renders EntityEvents with the loaded entity", () => {
    primeEntity({ id: "org-1", name: "Acme" });

    renderWithOrganizationRoute(<OrganizationEventsDetails />);

    expect(screen.getByTestId("entity-events")).toHaveTextContent("org-1");
  });

  it("renders nothing until the entity is loaded", () => {
    primeEntity(undefined);

    renderWithOrganizationRoute(<OrganizationEventsDetails />);

    expect(screen.queryByTestId("entity-events")).not.toBeInTheDocument();
  });
});
