import type { ComponentProps } from "react";

import { render, screen } from "@testing-library/react";

import type { OrganizationRead } from "~api/ffc-api-model";
import type { useOrganizationDetailsApi } from "~organizations/api";
import type { PageShell } from "~shared/components/page-shell";

import { OrganizationDetailsHeader } from "./OrganizationDetailsHeader";

type MockPageShellHeaderProps = ComponentProps<typeof PageShell.Header>;
type UseOrganizationDetailsApiResult = ReturnType<typeof useOrganizationDetailsApi>;

const mockUseOrganizationDetailsApi = jest.fn() as jest.MockedFunction<
  typeof useOrganizationDetailsApi
>;
const mockPageShellHeader = jest.fn() as jest.MockedFunction<
  (props: MockPageShellHeaderProps) => void
>;
const mockStatus = jest.fn() as jest.MockedFunction<(props: { item: unknown }) => void>;

jest.mock("~organizations/api", () => ({
  useOrganizationDetailsApi: (id: string | undefined) => mockUseOrganizationDetailsApi(id),
}));

jest.mock("~shared/components/page-shell", () => ({
  PageShell: {
    Header: (props: MockPageShellHeaderProps) => {
      mockPageShellHeader(props);
      return <div data-testid="page-shell-header">{"title" in props ? props.title : null}</div>;
    },
  },
}));

jest.mock("~shared/components/entity-status-chip", () => ({
  Status: (props: { item: unknown }) => {
    mockStatus(props);
    return <span data-testid="status" />;
  },
}));

function primeEntity(entity: Partial<OrganizationRead> | undefined) {
  mockUseOrganizationDetailsApi.mockReturnValue({
    data: entity,
  } as unknown as UseOrganizationDetailsApiResult);
}

function lastHeaderProps() {
  return mockPageShellHeader.mock.lastCall![0];
}

describe("OrganizationDetailsHeader", () => {
  it("queries organization details for the supplied organizationId", () => {
    primeEntity(undefined);

    render(<OrganizationDetailsHeader organizationId="org-1" backUrl="/back" />);

    expect(mockUseOrganizationDetailsApi).toHaveBeenCalledWith("org-1");
  });

  it("forwards backUrl to PageShell.Header", () => {
    primeEntity(undefined);

    render(<OrganizationDetailsHeader organizationId="org-1" backUrl="/back-here" />);

    expect(lastHeaderProps().backUrl).toBe("/back-here");
  });

  it("renders the entity id in the title and a Status chip when data is loaded", () => {
    primeEntity({ id: "org-1", name: "Acme", status: "active" });

    render(<OrganizationDetailsHeader organizationId="org-1" backUrl="/back" />);

    expect(screen.getByTestId("page-shell-header")).toBeInTheDocument();
    expect(screen.getByText("org-1")).toBeInTheDocument();
    expect(screen.getByTestId("status")).toBeInTheDocument();
    expect(mockStatus).toHaveBeenCalledWith(
      expect.objectContaining({ item: expect.objectContaining({ id: "org-1" }) }),
    );
  });

  it("does not render a Status chip when the entity has no id", () => {
    primeEntity({ name: "Acme" });

    render(<OrganizationDetailsHeader organizationId="org-1" backUrl="/back" />);

    expect(screen.queryByTestId("status")).not.toBeInTheDocument();
  });

  it("shows a name-based subtitle when the entity has a name", () => {
    primeEntity({ id: "org-1", name: "Acme" });

    render(<OrganizationDetailsHeader organizationId="org-1" backUrl="/back" />);

    expect(lastHeaderProps().subtitle).toBe("Organization Acme");
  });

  it("falls back to a generic subtitle when the entity has no name", () => {
    primeEntity({ id: "org-1" });

    render(<OrganizationDetailsHeader organizationId="org-1" backUrl="/back" />);

    expect(lastHeaderProps().subtitle).toBe("Organization details");
  });

  it("uses the entity name as avatar text when present", () => {
    primeEntity({ id: "org-1", name: "Acme" });

    render(<OrganizationDetailsHeader organizationId="org-1" backUrl="/back" />);

    expect(lastHeaderProps().avatar).toMatchObject({ text: "Acme", jdenticonValue: "org-1" });
  });

  it("falls back to '?' avatar text and empty jdenticonValue when entity is missing", () => {
    primeEntity(undefined);

    render(<OrganizationDetailsHeader organizationId="org-1" backUrl="/back" />);

    expect(lastHeaderProps().avatar).toMatchObject({ text: "?", jdenticonValue: "" });
  });

  it("uses the entity name as jdenticonValue when id is missing", () => {
    primeEntity({ name: "Acme" });

    render(<OrganizationDetailsHeader organizationId="org-1" backUrl="/back" />);

    expect(lastHeaderProps().avatar).toMatchObject({ jdenticonValue: "Acme" });
  });
});
