import type { ComponentProps } from "react";

import { render, screen } from "@testing-library/react";

import type { EntitlementRead } from "~api/ffc-api-model";
import type { useEntitlementsDetailsApi } from "~entitlements/api";
import { Status } from "~shared/components/entity-status-chip";
import type { PageShell } from "~shared/components/page-shell";

import { EntitlementDetailsHeader } from "./EntitlementDetailsHeader";

type MockPageShellHeaderProps = ComponentProps<typeof PageShell.Header>;
type MockStatusProps = ComponentProps<typeof Status>;
type UseEntitlementsDetailsApiResult = ReturnType<typeof useEntitlementsDetailsApi>;

const mockUseEntitlementsDetailsApi = jest.fn() as jest.MockedFunction<
  typeof useEntitlementsDetailsApi
>;
const mockPageShellHeader = jest.fn() as jest.MockedFunction<
  (props: MockPageShellHeaderProps) => void
>;
const mockStatus = jest.fn() as jest.MockedFunction<(props: MockStatusProps) => void>;

jest.mock("~entitlements/api", () => ({
  useEntitlementsDetailsApi: (id: string | undefined) => mockUseEntitlementsDetailsApi(id),
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
  Status: (props: MockStatusProps) => {
    mockStatus(props);
    return <span data-testid="status" />;
  },
}));

function primeEntity(entity: Partial<EntitlementRead> | undefined) {
  mockUseEntitlementsDetailsApi.mockReturnValue({
    data: entity,
  } as unknown as UseEntitlementsDetailsApiResult);
}

function lastHeaderProps() {
  return mockPageShellHeader.mock.lastCall![0];
}

describe("EntitlementDetailsHeader", () => {
  it("queries entitlement details for the supplied entitlementId", () => {
    primeEntity(undefined);

    render(<EntitlementDetailsHeader entitlementId="ent-1" backUrl="/back" />);

    expect(mockUseEntitlementsDetailsApi).toHaveBeenCalledWith("ent-1");
  });

  it("forwards backUrl to PageShell.Header", () => {
    primeEntity(undefined);

    render(<EntitlementDetailsHeader entitlementId="ent-1" backUrl="/back-here" />);

    expect(lastHeaderProps().backUrl).toBe("/back-here");
  });

  it("renders the entity id in the title and a Status chip when data is loaded", () => {
    primeEntity({ id: "ent-1", name: "One", status: "active" });

    render(<EntitlementDetailsHeader entitlementId="ent-1" backUrl="/back" />);

    expect(screen.getByText("ent-1")).toBeInTheDocument();
    expect(screen.getByTestId("status")).toBeInTheDocument();
    expect(mockStatus).toHaveBeenCalledWith(
      expect.objectContaining({ item: expect.objectContaining({ id: "ent-1" }) }),
    );
  });

  it("does not render a Status chip when the entity has no id", () => {
    primeEntity({ name: "no id" });

    render(<EntitlementDetailsHeader entitlementId="ent-1" backUrl="/back" />);

    expect(screen.queryByTestId("status")).not.toBeInTheDocument();
  });

  it("shows a name-based subtitle when the entity has a name", () => {
    primeEntity({ id: "ent-1", name: "One" });

    render(<EntitlementDetailsHeader entitlementId="ent-1" backUrl="/back" />);

    expect(lastHeaderProps().subtitle).toBe("Entitlement One");
  });

  it("falls back to a generic subtitle when the entity has no name", () => {
    primeEntity({ id: "ent-1" });

    render(<EntitlementDetailsHeader entitlementId="ent-1" backUrl="/back" />);

    expect(lastHeaderProps().subtitle).toBe("Entitlement details");
  });

  it("uses the entity name as avatar text when present", () => {
    primeEntity({ id: "ent-1", name: "One" });

    render(<EntitlementDetailsHeader entitlementId="ent-1" backUrl="/back" />);

    expect(lastHeaderProps().avatar).toMatchObject({ text: "One", jdenticonValue: "ent-1" });
  });

  it("falls back to '?' avatar text and empty jdenticonValue when entity is missing", () => {
    primeEntity(undefined);

    render(<EntitlementDetailsHeader entitlementId="ent-1" backUrl="/back" />);

    expect(lastHeaderProps().avatar).toMatchObject({ text: "?", jdenticonValue: "" });
  });

  it("uses the entity name as jdenticonValue when id is missing", () => {
    primeEntity({ name: "One" });

    render(<EntitlementDetailsHeader entitlementId="ent-1" backUrl="/back" />);

    expect(lastHeaderProps().avatar).toMatchObject({ jdenticonValue: "One" });
  });
});
