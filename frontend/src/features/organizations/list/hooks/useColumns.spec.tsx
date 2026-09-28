import { renderHook, screen } from "@testing-library/react";

import type { AccountType } from "~api/ffc-api-model";
import { columnByName, makeOrganization, renderColumnCell } from "~test-utils";

import { mockGetActions, mockStatus, mockUseUserRole } from "./useColumns.spec.mocks";

import { useColumns } from "./useColumns";

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
