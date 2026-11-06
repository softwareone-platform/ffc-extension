import type { ComponentProps } from "react";

import { screen } from "@testing-library/react";

import type { OrganizationRead } from "~api/ffc-api-model";
import type { useOrganizationDetailsApi } from "~organizations/api";
import type { DataSourceHighlights } from "~organizations/components/DataSourceHighlights";
import type { OrganizationHighlights } from "~organizations/components/OrganizationHighlights";
import type { OrganizationsProvider } from "~organizations/providers/OrganizationsProvider";
import { renderWithOrganizationRoute, renderWithRouter } from "~test-utils";

import { OrganizationDetailsContent } from "./DetailsContent";

type ApiResult = ReturnType<typeof useOrganizationDetailsApi>;
type MockOrganizationHighlightsProps = ComponentProps<typeof OrganizationHighlights>;
type MockDataSourceHighlightsProps = ComponentProps<typeof DataSourceHighlights>;
type MockNavigationTopBarProps = ComponentProps<
  typeof import("@swo/design-system/navigation").Navigation.TopBar
>;
type MockCardProps = ComponentProps<typeof import("@swo/design-system/card").Card>;

const mockUseOrganizationDetailsApi = jest.fn() as jest.MockedFunction<
  typeof useOrganizationDetailsApi
>;
const mockOrganizationHighlights = jest.fn() as jest.MockedFunction<
  (props: MockOrganizationHighlightsProps) => void
>;
const mockDataSourceHighlights = jest.fn() as jest.MockedFunction<
  (props: MockDataSourceHighlightsProps) => void
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

jest.mock("../components/DataSourceHighlights", () => ({
  DataSourceHighlights: (props: MockDataSourceHighlightsProps) => {
    mockDataSourceHighlights(props);
    return <div data-testid="data-source-highlights" />;
  },
}));

jest.mock("../providers/OrganizationsProvider", () => ({
  OrganizationsProvider: (props: ComponentProps<typeof OrganizationsProvider>) => {
    mockOrganizationsProvider(props);
    return <div data-testid="organizations-provider">{props.children}</div>;
  },
}));

jest.mock("@swo/design-system/card", () => ({
  Card: ({ children }: MockCardProps) => <div data-testid="card">{children}</div>,
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

  it("renders DataSourceHighlights instead of OrganizationHighlights on a data source route", () => {
    primeEntity({ id: "org-1" });

    renderWithOrganizationRoute(<OrganizationDetailsContent />, {
      initialUrl: "/organizations/org-1/data-sources/ds-1/details",
      routePath: "/organizations/:organizationId/data-sources/:dataSourceId/*",
    });

    expect(mockDataSourceHighlights).toHaveBeenCalledWith({
      organizationId: "org-1",
      dataSourceId: "ds-1",
    });
    expect(mockOrganizationHighlights).not.toHaveBeenCalled();
  });

  it("renders the data source tabs in the top bar on a data source route", () => {
    primeEntity({ id: "org-1" });

    renderWithOrganizationRoute(<OrganizationDetailsContent />, {
      initialUrl: "/organizations/org-1/data-sources/ds-1/details",
      routePath: "/organizations/:organizationId/data-sources/:dataSourceId/*",
    });

    const paths = mockTopBar.mock.lastCall![0].items!.map((item) => item.path);
    expect(paths).toEqual(["data-sources/ds-1/details", "data-sources/ds-1/advanced"]);
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

  it("renders the organization tabs in the top bar in order", () => {
    primeEntity({ id: "org-1" });

    renderWithOrganizationRoute(<OrganizationDetailsContent />, {
      routePath: "/organizations/:organizationId/*",
    });

    const paths = mockTopBar.mock.lastCall![0].items!.map((item) => item.path);
    expect(paths).toEqual(["general", "data-sources", "users", "events", "logs"]);
  });

  it("shows the termination tab before logs when the organization has termination feedback", () => {
    primeEntity({ id: "org-1", termination_feedback: { id: "tf-1", reason: "other" } });

    renderWithOrganizationRoute(<OrganizationDetailsContent />, {
      routePath: "/organizations/:organizationId/*",
    });

    const paths = mockTopBar.mock.lastCall![0].items!.map((item) => item.path);
    expect(paths).toEqual(["general", "data-sources", "users", "events", "termination", "logs"]);
  });

  it.each([
    ["is null", null],
    ["is missing", undefined],
  ])("hides the termination tab when the termination feedback %s", (_, terminationFeedback) => {
    primeEntity({ id: "org-1", termination_feedback: terminationFeedback });

    renderWithOrganizationRoute(<OrganizationDetailsContent />, {
      routePath: "/organizations/:organizationId/*",
    });

    const paths = mockTopBar.mock.lastCall![0].items!.map((item) => item.path);
    expect(paths).not.toContain("termination");
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
