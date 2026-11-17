import { renderHook } from "@testing-library/react";

import { useViews } from "./useViews";

describe("useViews (organization event logs)", () => {
  it("returns info, warning and error views in fixed order", () => {
    const { result } = renderHook(() => useViews());

    expect(result.current.map((v) => v.name)).toEqual(["logInfo", "logWarning", "logError"]);
  });

  it.each([
    ["logInfo", "INFO"],
    ["logWarning", "WARNING"],
    ["logError", "ERROR"],
  ])("scopes the %s view to level '%s' sorted by newest first", (viewName, level) => {
    const { result } = renderHook(() => useViews());
    const view = result.current.find((v) => v.name === viewName)!;

    expect(view.configuration).toEqual({
      filters: {
        operator: "and",
        value: [{ operator: "eq", field: "level", value: level }],
      },
      sort: [{ field: "time", direction: "desc" }],
    });
  });
});
