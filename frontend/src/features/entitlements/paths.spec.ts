import { PATHS } from "./paths";

describe("entitlements paths", () => {
  it.each([
    ["detail", "/entitlements/ent-1"],
    ["general", "/entitlements/ent-1/general"],
    ["events", "/entitlements/ent-1/events"],
  ] as const)("builds the %s URL from an entitlement id", (key, expected) => {
    const builder = PATHS[key] as (id: string) => string;
    expect(builder("ent-1")).toBe(expected);
  });

  it("detailMatch is the react-router pattern for the detail route", () => {
    expect(PATHS.detailMatch).toBe("/entitlements/:entitlementId/*");
  });
});
