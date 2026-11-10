import { renderHook } from "@testing-library/react";

import type { GridFieldDefinition } from "@swo/design-system/grid";

import { useFields } from "./useFields";

function getField(name: string) {
  const { result } = renderHook(() => useFields());
  return result.current.find((f) => f.name === name) as GridFieldDefinition;
}

describe("useFields (organization event logs)", () => {
  it("returns fields in fixed order", () => {
    const { result } = renderHook(() => useFields());

    expect(result.current.map((f) => f.name)).toEqual([
      "time",
      "level",
      "description",
      "evt_class",
      "object_id",
      "object_name",
    ]);
  });

  it("marks time as a date field", () => {
    expect(getField("time")).toMatchObject({ type: "date" });
  });

  it("exposes level as a filterable list of INFO, WARNING and ERROR", () => {
    const level = getField("level");

    expect(level).toMatchObject({ type: "list", allowedOperations: ["Filter"] });
    expect(level.options!.map((o) => o.value)).toEqual(["INFO", "WARNING", "ERROR"]);
  });

  it("exposes evt_class as a list of unique event classes labelled by their key", () => {
    const evtClass = getField("evt_class");
    const values = evtClass.options!.map((o) => o.value);

    expect(evtClass).toMatchObject({ type: "list" });
    expect(new Set(values).size).toBe(values.length);
    expect(evtClass.options!.every((o) => o.label === o.value)).toBe(true);
  });

  it.each([
    ["object_id", ["Filter"]],
    ["description", []],
    ["evt_class", []],
    ["object_name", []],
  ])("restricts '%s' to operations %j", (name, allowedOperations) => {
    expect(getField(name).allowedOperations).toEqual(allowedOperations);
  });
});
