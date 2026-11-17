import { ReactNode } from "react";

import { renderHook } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";

import { useViews } from "./useViews";

function renderViews(url = "/organizations") {
  return renderHook(() => useViews(), {
    wrapper: ({ children }: { children: ReactNode }) => (
      <MemoryRouter initialEntries={[url]}>{children}</MemoryRouter>
    ),
  });
}

describe("useViews (organizations list)", () => {
  it("returns main, active, and deleted views in fixed order", () => {
    const { result } = renderViews();

    expect(result.current.map((v) => v.name)).toEqual(["main", "active", "deleted"]);
  });

  it("configures the main view to exclude deleted organizations sorted by most recent update", () => {
    const { result } = renderViews();
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
    const { result } = renderViews();
    const view = result.current.find((v) => v.name === viewName)!;

    expect(view.configuration).toMatchObject({
      filters: {
        operator: "and",
        value: [{ operator: "eq", field: "status", value: statusValue }],
      },
      sort: [{ field: "name", direction: "asc" }],
    });
  });

  it("replaces the main view filter with the statuses passed in the URL", () => {
    const { result } = renderViews("/organizations?statuses=active,terminated");
    const main = result.current.find((v) => v.name === "main")!;

    expect(main.configuration.filters).toEqual({
      operator: "or",
      value: [
        { operator: "eq", field: "status", value: "active" },
        { operator: "eq", field: "status", value: "terminated" },
      ],
    });
  });

  it("ignores unknown statuses in the URL and keeps the default main filter", () => {
    const { result } = renderViews("/organizations?statuses=bogus");
    const main = result.current.find((v) => v.name === "main")!;

    expect(main.configuration.filters).toEqual({
      operator: "or",
      value: [{ operator: "neq", field: "status", value: "deleted" }],
    });
  });
});
