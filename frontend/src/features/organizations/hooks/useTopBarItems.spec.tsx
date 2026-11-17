import { renderHook } from "@testing-library/react";

import type { OrganizationRead } from "~api/ffc-api-model";
import { makeOrganization } from "~test-utils/factories";

import { useTopBarItems } from "./useTopBarItems";

function getItems(props: Parameters<typeof useTopBarItems>[0]) {
  return renderHook(() => useTopBarItems(props)).result.current;
}

describe("useTopBarItems", () => {
  it("returns details and advanced tabs scoped to the data source when a routeId is given", () => {
    const items = getItems({ routeId: "ds-1" });

    expect(items.map(({ label, path }) => ({ label, path }))).toEqual([
      { label: "dataSource:details", path: "data-sources/ds-1/details" },
      { label: "dataSource:advanced", path: "data-sources/ds-1/advanced" },
    ]);
  });

  it("returns the organization tabs without termination when there is no termination feedback", () => {
    const items = getItems({ entity: { id: "org-1" } as OrganizationRead });

    expect(items.map((item) => item.path)).toEqual([
      "general",
      "data-sources",
      "users",
      "events",
      "logs",
    ]);
  });

  it("inserts the termination tab before logs when the organization has termination feedback", () => {
    const entity = {
      id: "org-1",
      termination_feedback: { id: "tf-1", reason: "other" },
    } as OrganizationRead;

    const items = getItems({ entity });

    expect(items.map((item) => item.path)).toEqual([
      "general",
      "data-sources",
      "users",
      "events",
      "termination",
      "logs",
    ]);
  });

  it("ignores the organization's termination feedback when a routeId is given", () => {
    const entity = {
      id: "org-1",
      termination_feedback: { id: "tf-1", reason: "other" },
    } as OrganizationRead;

    const items = getItems({ entity, routeId: "ds-1" });

    expect(items.map((item) => item.path)).not.toContain("termination");
  });

  it.each([
    ["without termination feedback", undefined, ["general", "events"]],
    [
      "with termination feedback",
      { id: "tf-1", reason: "other" },
      ["general", "events", "termination"],
    ],
  ] as const)(
    "hides the data sources, users and logs tabs for a deleted organization %s",
    (_, terminationFeedback, expectedPaths) => {
      const entity = makeOrganization({
        status: "deleted",
        termination_feedback: terminationFeedback,
      });

      const items = getItems({ entity });

      expect(items.map((item) => item.path)).toEqual(expectedPaths);
    },
  );

  it.each(["active", "terminated"] as const)(
    "keeps the data sources, users and logs tabs for an organization with status '%s'",
    (status) => {
      const items = getItems({ entity: makeOrganization({ status }) });

      expect(items.map((item) => item.path)).toEqual(
        expect.arrayContaining(["data-sources", "users", "logs"]),
      );
    },
  );
});
