import { renderHook } from "@testing-library/react";

import { useViews } from "./useViews";

describe("useViews (organizations list)", () => {
  it("returns main, active, and deleted views in fixed order", () => {
    const { result } = renderHook(() => useViews());

    expect(result.current.map((v) => v.name)).toEqual(["main", "active", "deleted"]);
  });

  it("configures the main view to exclude deleted organizations sorted by most recent update", () => {
    const { result } = renderHook(() => useViews());
    const main = result.current.find((v) => v.name === "main")!;

    expect(main.configuration).toMatchObject({
      filters: {
        operator: "or",
        value: [{ operator: "neq", field: "status", value: "deleted" }],
      },
      sort: [{ field: "events.updated.at", direction: "desc" }],
    });
  });

  it.each([
    ["active", "active"],
    ["deleted", "deleted"],
  ])("scopes the %s view to status='%s' sorted by name asc", (viewName, statusValue) => {
    const { result } = renderHook(() => useViews());
    const view = result.current.find((v) => v.name === viewName)!;

    expect(view.configuration).toMatchObject({
      filters: {
        operator: "and",
        value: [{ operator: "eq", field: "status", value: statusValue }],
      },
      sort: [{ field: "name", direction: "asc" }],
    });
  });
});
