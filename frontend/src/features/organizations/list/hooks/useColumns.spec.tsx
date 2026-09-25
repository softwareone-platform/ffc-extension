import type { ReactNode } from "react";

import { renderHook, screen } from "@testing-library/react";

import type { AccountType } from "~api/ffc-api-model";
import type { useUserRole } from "~shared/hooks/useUserRole";
import { columnByName, makeOrganization, renderColumnCell } from "~test-utils";
import { mockDesignSystemGrid } from "~test-utils/mocks/designSystemGrid";
import { mockGridCellDynamicActions } from "~test-utils/mocks/sharedGridCells";

import type { useActionOptions } from "./useActionOptions";
import { useColumns } from "./useColumns";

const mockUseUserRole = jest.fn() as jest.MockedFunction<typeof useUserRole>;
const mockGetActions = jest.fn() as jest.MockedFunction<ReturnType<typeof useActionOptions>>;
const mockStatus = jest.fn() as jest.MockedFunction<(props: { item: unknown }) => void>;

jest.mock("@swo/design-system/grid", () => ({
  ...mockDesignSystemGrid,
  GridCellDateTime: ({ date }: { date?: string }) => (
    <span data-testid="grid-cell-date-time">{date ?? "no-date"}</span>
  ),
  GridCellTitleSubtitle: ({ title, subtitle }: { title: ReactNode; subtitle: ReactNode }) => (
    <div data-testid="grid-cell-title-subtitle">
      <span data-testid="title">{title}</span>
      <span data-testid="subtitle">{subtitle}</span>
    </div>
  ),
}));

jest.mock("~shared/components/entity-status-chip/EntityStatusChip", () => ({
  Status: (props: { item: unknown }) => {
    mockStatus(props);
    return <span data-testid="status" />;
  },
}));

jest.mock("~shared/components/grid/GridCellDynamicActions", () => mockGridCellDynamicActions);

jest.mock("~shared/hooks/useUserRole", () => ({
  useUserRole: () => mockUseUserRole(),
}));

jest.mock("react-router-dom", () => {
  const actual = jest.requireActual("react-router-dom");
  return { ...actual, Link: ({ children }: { children?: ReactNode }) => <>{children}</> };
});

jest.mock("./useActionOptions", () => ({
  useActionOptions: () => mockGetActions,
}));

const COLUMN_FIELDS = [
  ["name", ["name", "id"]],
  ["currency", ["currency"]],
  ["billing_currency", ["billing_currency"]],
  ["linked_organization_id", ["linked_organization_id"]],
  ["operations_external_id", ["operations_external_id"]],
  ["updated_at", ["events.updated.at"]],
  ["created_at", ["events.created.at"]],
  ["terminated_at", ["events.terminated.at"]],
  ["deleted_at", ["events.deleted.at"]],
  ["deletable_at", ["deletable_at"]],
  ["status", ["status"]],
  ["actions", []],
] as const;

describe("useColumns (organizations list)", () => {
  beforeEach(() => {
    mockUseUserRole.mockReturnValue({ user: null, role: "admin" });
  });

  it("returns columns in fixed order", () => {
    const { result } = renderHook(() => useColumns());

    expect(result.current.map((c) => c.name)).toEqual(COLUMN_FIELDS.map(([name]) => name));
  });

  it.each(COLUMN_FIELDS)("column '%s' maps to fields %j", (name, expectedFields) => {
    const { result } = renderHook(() => useColumns());

    expect(columnByName(result.current, name).fields).toEqual(expectedFields);
  });

  it.each<[AccountType, boolean]>([
    ["operations", true],
    ["admin", false],
  ])("hides the actions column for role '%s' → isHidden=%s", (role, isHidden) => {
    mockUseUserRole.mockReturnValue({ user: null, role });
    const { result } = renderHook(() => useColumns());

    expect(columnByName(result.current, "actions").isHidden).toBe(isHidden);
  });

  it("renders the name column with a link title and id | linked_organization_id subtitle", () => {
    const { result } = renderHook(() => useColumns());

    renderColumnCell(
      result.current,
      "name",
      makeOrganization({ id: "org-1", name: "Acme", linked_organization_id: "linked-1" }),
    );

    expect(screen.getByTestId("title")).toHaveTextContent("Acme");
    expect(screen.getByTestId("subtitle")).toHaveTextContent("org-1 | linked-1");
  });

  it.each([
    ["updated_at", "updated"],
    ["created_at", "created"],
    ["terminated_at", "terminated"],
    ["deleted_at", "deleted"],
  ] as const)("renders '%s' column with GridCellDateTime", (columnName, key) => {
    const { result } = renderHook(() => useColumns());
    const events = { [key]: { at: "2026-01-15T10:00:00Z" } } as never;

    renderColumnCell(result.current, columnName, makeOrganization({ events }));

    expect(screen.getByTestId("grid-cell-date-time")).toHaveTextContent("2026-01-15T10:00:00Z");
  });

  it("renders the status column with a Status chip", () => {
    const { result } = renderHook(() => useColumns());
    const item = makeOrganization({ status: "active" });

    renderColumnCell(result.current, "status", item);

    expect(mockStatus).toHaveBeenCalledWith({ item });
  });

  it("renders the actions column with dynamic actions for the item", () => {
    mockGetActions.mockReturnValue([{ value: "edit", label: "edit" }]);
    const { result } = renderHook(() => useColumns());
    const item = makeOrganization();

    renderColumnCell(result.current, "actions", item);

    expect(screen.getByTestId("actions-item-id")).toHaveTextContent(item.id);
    expect(screen.getByTestId("actions-count")).toHaveTextContent("1");
    expect(mockGetActions).toHaveBeenCalledWith(item);
  });
});
