import type { ComponentProps } from "react";

import { render, screen } from "@testing-library/react";

import type { DisplayValue } from "@swo/design-system/utils";

import { highlightValues } from "~test-utils";
import {
  mockDesignSystemUtils,
  mockDesignSystemUtilsGlobals,
} from "~test-utils/mocks/designSystemUtils";
import { mockEntityReferenceCell } from "~test-utils/mocks/entityReferenceCell";
import { mockFormatDateModule } from "~test-utils/mocks/formatDate";
import { mockDesignSystemInPageHighlight } from "~test-utils/mocks/inPageHighlight";

import { EntityProperties, type EntityProperty } from "./EntityProperties";

type MockDisplayValueProps = Pick<ComponentProps<typeof DisplayValue>, "value" | "context">;

jest.mock("@swo/design-system/in-page-highlight", () => mockDesignSystemInPageHighlight);
jest.mock("@swo/design-system/entity-reference-cell", () => mockEntityReferenceCell);
// Mirrors the real DisplayValue falsy-value fallback (bypassed only in the "financial" context),
// so the zero-number case proves the component opts out of it.
jest.mock("@swo/design-system/utils", () => ({
  ...mockDesignSystemUtils,
  DisplayValue: ({ value, context }: MockDisplayValueProps) => (
    <>
      {value == null || (!value && context !== "financial")
        ? mockDesignSystemUtils.NO_VALUE
        : String(value)}
    </>
  ),
}));
jest.mock("~shared/hooks/useFormatDate", () => mockFormatDateModule);

const { NO_VALUE } = mockDesignSystemUtilsGlobals;

function renderProperties(properties: EntityProperty[]) {
  return render(<EntityProperties properties={properties} />);
}

describe("EntityProperties", () => {
  it("renders one highlight item per property in the given order", () => {
    renderProperties([
      { label: "first", value: "a", type: "string" },
      { label: "second", value: "b", type: "raw" },
    ]);

    expect(Object.keys(highlightValues())).toEqual(["first", "second"]);
  });

  it("hides properties whose condition is false", () => {
    renderProperties([
      { label: "shown", value: "a", type: "string", condition: true },
      { label: "hidden", value: "b", type: "string", condition: false },
      { label: "unconditional", value: "c", type: "string" },
    ]);

    expect(highlightValues()).toEqual({ shown: "a", unconditional: "c" });
  });

  it.each([
    ["string", "value-1", "value-1"],
    ["number", 42, "42"],
    ["raw", "raw-value", "raw-value"],
  ] as const)("renders a %s property value as-is", (type, value, expected) => {
    renderProperties([{ label: "prop", value, type }]);

    expect(highlightValues().prop).toBe(expected);
  });

  it("renders a zero number value instead of NO_VALUE", () => {
    renderProperties([{ label: "count", value: 0, type: "number" }]);

    expect(highlightValues().count).toBe("0");
  });

  it.each([
    [true, "yes"],
    [false, "no"],
  ])("renders a boolean %s value as a yes / no label", (value, expected) => {
    renderProperties([{ label: "flag", value, type: "boolean" }]);

    expect(highlightValues().flag).toBe(expected);
  });

  it("shows NO_VALUE for a boolean property whose value is not a boolean", () => {
    renderProperties([{ label: "flag", value: "true", type: "boolean" }]);

    expect(highlightValues().flag).toBe(NO_VALUE);
  });

  it.each([
    ["undefined", undefined],
    ["null", null],
    ["an empty string", ""],
  ])("shows NO_VALUE when the value is %s", (_, value) => {
    renderProperties([{ label: "prop", value, type: "string" }]);

    expect(highlightValues().prop).toBe(NO_VALUE);
  });

  it("formats an ISO string date value", () => {
    renderProperties([{ label: "connected_at", value: "2026-01-15T10:00:00Z", type: "date" }]);

    expect(highlightValues().connected_at).toBe("date(2026-01-15T10:00:00Z)");
  });

  it("formats a Date instance value", () => {
    const date = new Date("2026-01-15T10:00:00Z");

    renderProperties([{ label: "connected_at", value: date, type: "date" }]);

    expect(highlightValues().connected_at).toBe(`date(${String(date)})`);
  });

  it("shows NO_VALUE for a date property whose value is not a date", () => {
    renderProperties([{ label: "connected_at", value: 12345, type: "date" }]);

    expect(highlightValues().connected_at).toBe(NO_VALUE);
  });

  it("renders an entity reference with its primary, secondary and icon content", () => {
    renderProperties([
      {
        label: "parent",
        type: "entity",
        value: {
          primaryContent: "Parent name",
          secondaryContent: "parent-123",
          icon: <svg data-testid="parent-icon" />,
        },
      },
    ]);

    expect(screen.getByTestId("primary")).toHaveTextContent("Parent name");
    expect(screen.getByTestId("secondary")).toHaveTextContent("parent-123");
    expect(screen.getByTestId("parent-icon")).toBeInTheDocument();
  });

  it("falls back to NO_VALUE as entity secondary content when none is provided", () => {
    renderProperties([{ label: "parent", type: "entity", value: { primaryContent: "Parent" } }]);

    expect(screen.getByTestId("secondary")).toHaveTextContent(NO_VALUE);
  });

  it("shows NO_VALUE instead of an entity reference when the entity is missing", () => {
    renderProperties([{ label: "parent", type: "entity", value: null }]);

    expect(screen.queryByTestId("entity-reference-cell")).not.toBeInTheDocument();
    expect(highlightValues().parent).toBe(NO_VALUE);
  });
});
