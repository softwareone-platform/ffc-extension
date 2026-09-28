import type { ComponentProps, ReactNode } from "react";

import { screen } from "@testing-library/react";

import type { OrganizationRead } from "~api/ffc-api-model";
import type { useOrganizationDetailsApi } from "~organizations/api";
import type { OrganizationHighlights } from "~organizations/components/OrganizationHighlights";
import type { OrganizationsProvider } from "~organizations/providers/OrganizationsProvider";
import { renderWithOrganizationRoute, renderWithRouter } from "~test-utils";

import { OrganizationDetailsContent } from "./DetailsContent";

type ApiResult = ReturnType<typeof useOrganizationDetailsApi>;
type MockOrganizationHighlightsProps = ComponentProps<typeof OrganizationHighlights>;
type MockNavigationTopBarProps = ComponentProps<
  typeof import("@swo/design-system/navigation").Navigation.TopBar
>;

const mockUseOrganizationDetailsApi = jest.fn() as jest.MockedFunction<
  typeof useOrganizationDetailsApi
>;
const mockOrganizationHighlights = jest.fn() as jest.MockedFunction<
  (props: MockOrganizationHighlightsProps) => void
>;
const mockTopBar = jest.fn() as jest.MockedFunction<(props: MockNavigationTopBarProps) => void>;
const mockOrganizationsProvider = jest.fn() as jest.MockedFunction<
  (props: ComponentProps<typeof OrganizationsProvider>) => void
>;

jest.mock("~organizations/api", () => ({
  useOrganizationDetailsApi: (id: string | undefined) => mockUseOrganizationDetailsApi(id),
}));

jest.mock("../components/OrganizationHighlights", () => ({
  OrganizationHighlights: (props: MockOrganizationHighlightsProps) => {
    mockOrganizationHighlights(props);
    return <div data-testid="organization-highlights">{props.organizationId}</div>;
  },
}));

jest.mock("../providers/OrganizationsProvider", () => ({
  OrganizationsProvider: (props: ComponentProps<typeof OrganizationsProvider>) => {
    mockOrganizationsProvider(props);
    return <div data-testid="organizations-provider">{props.children}</div>;
  },
}));

jest.mock("@swo/design-system/card", () => ({
  Card: ({ children }: { children?: ReactNode }) => <div data-testid="card">{children}</div>,
}));

jest.mock("@swo/design-system/navigation", () => ({
  Navigation: {
    TopBar: (props: MockNavigationTopBarProps) => {
      mockTopBar(props);
      return <nav data-testid="top-bar" />;
    },
  },
}));

function primeEntity(entity: Partial<OrganizationRead> | undefined) {
  mockUseOrganizationDetailsApi.mockReturnValue({ data: entity } as unknown as ApiResult);
}

describe("OrganizationDetailsContent", () => {
  it("queries organization details using the organizationId route param", () => {
    primeEntity({ id: "org-1" });

    renderWithOrganizationRoute(<OrganizationDetailsContent />, {
      routePath: "/organizations/:organizationId/*",
    });

    expect(mockUseOrganizationDetailsApi).toHaveBeenCalledWith("org-1");
  });

  it("renders OrganizationHighlights with the organizationId when the param is present", () => {
    primeEntity({ id: "org-1" });

    renderWithOrganizationRoute(<OrganizationDetailsContent />, {
      routePath: "/organizations/:organizationId/*",
    });

    expect(mockOrganizationHighlights).toHaveBeenCalledWith({ organizationId: "org-1" });
  });

  it("omits OrganizationHighlights when the organizationId param is missing", () => {
    primeEntity(undefined);

    renderWithRouter(<OrganizationDetailsContent />, {
      initialUrl: "/organizations",
      routePath: "/organizations",
    });

    expect(mockOrganizationHighlights).not.toHaveBeenCalled();
    expect(screen.queryByTestId("organization-highlights")).not.toBeInTheDocument();
  });

  it("renders the top bar with items for general, dataSources, users, and events in order", () => {
    primeEntity({ id: "org-1" });

    renderWithOrganizationRoute(<OrganizationDetailsContent />, {
      routePath: "/organizations/:organizationId/*",
    });

    const paths = mockTopBar.mock.lastCall![0].items!.map((item) => item.path);
    expect(paths).toEqual(["general", "data-sources", "users", "events"]);
  });

  it("passes the loaded entity into the OrganizationsProvider", () => {
    const entity = { id: "org-1", name: "Acme" } as OrganizationRead;
    primeEntity(entity);

    renderWithOrganizationRoute(<OrganizationDetailsContent />, {
      routePath: "/organizations/:organizationId/*",
    });

    expect(mockOrganizationsProvider).toHaveBeenCalledWith(
      expect.objectContaining({ organization: entity }),
    );
  });
});
