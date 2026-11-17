import type { DatasourceDetailRead } from "~api/ffc-api-model";

import { getPropertyValue } from "./PropertiesUtils";

function makeDetailRead(details: DatasourceDetailRead["details"]) {
  return { id: "ds-1", details } as DatasourceDetailRead;
}

describe("getPropertyValue", () => {
  it("returns the value of a property present in the entity details", () => {
    const entity = makeDetailRead({ tenant_id: "tenant-1" });

    expect(getPropertyValue(entity, "tenant_id")).toBe("tenant-1");
  });

  it("returns undefined when the property is not present in the details", () => {
    const entity = makeDetailRead({ tenant_id: "tenant-1" });

    expect(getPropertyValue(entity, "project_id")).toBeUndefined();
  });

  it.each([
    ["the entity is null", null],
    ["the entity is undefined", undefined],
    ["the entity has no details", makeDetailRead(undefined)],
  ])("returns undefined when %s", (_, entity) => {
    expect(getPropertyValue(entity, "tenant_id")).toBeUndefined();
  });
});
