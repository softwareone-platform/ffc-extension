import { renderHook } from "@testing-library/react";

import type { GridFieldDefinition } from "@swo/design-system/grid";

import { useFields } from "./useFields";

describe("useFields (organizations list)", () => {
  it("returns fields in fixed order", () => {
    const { result } = renderHook(() => useFields());

    expect(result.current.map((f) => f.name)).toEqual([
      "id",
      "name",
      "currency",
      "billing_currency",
      "operations_external_id",
      "linked_organization_id",
      "events.created.at",
      "events.terminated.at",
      "events.deleted.at",
      "events.updated.at",
      "status",
    ]);
  });

  it.each(["events.created.at", "events.terminated.at", "events.deleted.at", "events.updated.at"])(
    "marks '%s' as a date field",
    (name) => {
      const { result } = renderHook(() => useFields());
      const field = result.current.find((f) => f.name === name);

      expect(field).toMatchObject({ type: "date" });
    },
  );

  it("exposes status as a list field with active/terminated/deleted options", () => {
    const { result } = renderHook(() => useFields());
    const status = result.current.find((f) => f.name === "status") as GridFieldDefinition;

    expect(status).toMatchObject({ type: "list" });
    expect(status.options!.map((o) => o.value)).toEqual(["active", "terminated", "deleted"]);
  });
});
