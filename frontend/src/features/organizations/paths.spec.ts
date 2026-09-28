import { PATHS } from "./paths";

describe("organizations paths", () => {
  it.each([
    ["detail", "/organizations/org-1"],
    ["general", "/organizations/org-1/general"],
    ["events", "/organizations/org-1/events"],
    ["dataSources", "/organizations/org-1/data-sources"],
    ["users", "/organizations/org-1/users"],
  ] as const)("builds the %s URL from an organization id", (key, expected) => {
    const builder = PATHS[key] as (id: string) => string;
    expect(builder("org-1")).toBe(expected);
  });

  it("exposes the react-router pattern for organization details", () => {
    expect(PATHS.detailMatch).toBe("/organizations/:organizationId/*");
  });
});
