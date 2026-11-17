import { renderHook, screen } from "@testing-library/react";

import type { OrganizationEventRead } from "~api/ffc-api-model";
import { columnByName, renderColumnCell } from "~test-utils";
import { mockDesignSystemGrid } from "~test-utils/mocks/designSystemGrid";
import { mockEntityStatusChip } from "~test-utils/mocks/entityStatusChip";

import { useColumns } from "./useColumns";

jest.mock("@swo/design-system/grid", () => mockDesignSystemGrid);
jest.mock("~shared/components/entity-status-chip", () => mockEntityStatusChip);

const COLUMN_FIELDS = [
  ["time", ["time"]],
  ["level", ["level"]],
  ["description", ["description"]],
  ["evt_class", ["evt_class"]],
  ["object_id", ["object_id"]],
  ["object_name", ["object_name"]],
] as const;

function makeEvent(overrides: Partial<OrganizationEventRead> = {}): OrganizationEventRead {
  return {
    id: "evt-1",
    time: "2026-11-06T09:00:00Z",
    level: "INFO",
    evt_class: "ORGANIZATION_CREATED",
    object_id: "obj-1",
    object_name: "Acme",
    description: "Organization created",
    ack: false,
    ...overrides,
  };
}

function getColumns() {
  return renderHook(() => useColumns()).result.current;
}

describe("useColumns (organization event logs)", () => {
  it("returns columns in fixed order", () => {
    expect(getColumns().map((c) => c.name)).toEqual(COLUMN_FIELDS.map(([name]) => name));
  });

  it.each(COLUMN_FIELDS)("column '%s' maps to fields %j", (name, expectedFields) => {
    expect(columnByName(getColumns(), name).fields).toEqual(expectedFields);
  });

  it.each([
    ["time", false],
    ["level", false],
    ["description", false],
    ["evt_class", true],
    ["object_id", true],
    ["object_name", true],
  ])("sets the initial visibility of the '%s' column", (name, isHidden) => {
    expect(Boolean(columnByName(getColumns(), name).isHidden)).toBe(isHidden);
  });

  it("renders the time column as a date-time cell", () => {
    renderColumnCell(getColumns(), "time", makeEvent());

    expect(screen.getByTestId("grid-cell-date-time")).toHaveTextContent("2026-11-06T09:00:00Z");
  });

  it.each([
    ["INFO", "info"],
    ["WARNING", "warning"],
    ["ERROR", "error"],
    ["UNKNOWN", "unknown"],
  ] as const)("renders level '%s' as a '%s' status chip", (level, status) => {
    renderColumnCell(getColumns(), "level", makeEvent({ level }));

    expect(screen.getByTestId("status")).toHaveTextContent(status);
  });

  it("renders the event class translated by its lower-cased key", () => {
    renderColumnCell(getColumns(), "evt_class", makeEvent({ evt_class: "ORGANIZATION_CREATED" }));

    expect(screen.getByTestId("grid-cell-simple")).toHaveTextContent("organization_created");
  });

  it.each([
    ["description", "Organization created"],
    ["object_id", "obj-1"],
    ["object_name", "Acme"],
  ])("renders the '%s' column as plain text", (name, expected) => {
    renderColumnCell(getColumns(), name, makeEvent());

    expect(screen.getByTestId("grid-cell-simple")).toHaveTextContent(expected);
  });

  it.each(["description", "object_id", "object_name"] as const)(
    "renders an empty '%s' cell when the value is missing",
    (name) => {
      renderColumnCell(getColumns(), name, makeEvent({ [name]: null }));

      expect(screen.getByTestId("grid-cell-simple")).toBeEmptyDOMElement();
    },
  );
});
