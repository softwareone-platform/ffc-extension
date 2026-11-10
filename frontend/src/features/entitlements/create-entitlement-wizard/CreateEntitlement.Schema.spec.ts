import { AddWizardFormSchema, toDatasourceIdRegExp } from "./CreateEntitlement.Schema";

describe("AddWizardFormSchema", () => {
  const validInput = {
    id: null,
    name: "My entitlement",
    affiliate: { id: "aff-1", name: "Affiliate 1", integration: null },
    dataSource: { id: "ds-1", affiliate_external_id: "ext-1" },
  };

  it("accepts a valid payload", () => {
    expect(AddWizardFormSchema.safeParse(validInput).success).toBe(true);
  });

  it("accepts an empty string for id since it is nullish", () => {
    const result = AddWizardFormSchema.safeParse({ ...validInput, id: undefined });
    expect(result.success).toBe(true);
  });

  it("rejects when name is missing", () => {
    const { name: _name, ...rest } = validInput;
    const result = AddWizardFormSchema.safeParse(rest);
    expect(result.success).toBe(false);
  });

  it("rejects when affiliate is missing", () => {
    const { affiliate: _affiliate, ...rest } = validInput;
    const result = AddWizardFormSchema.safeParse(rest);
    expect(result.success).toBe(false);
  });

  it("rejects when affiliate.id is missing", () => {
    const result = AddWizardFormSchema.safeParse({
      ...validInput,
      affiliate: { name: "no id", integration: null },
    });
    expect(result.success).toBe(false);
  });

  it("rejects when dataSource.id is missing", () => {
    const result = AddWizardFormSchema.safeParse({
      ...validInput,
      dataSource: { affiliate_external_id: "ext-1" },
    });
    expect(result.success).toBe(false);
  });

  it("rejects when dataSource.affiliate_external_id is missing", () => {
    const result = AddWizardFormSchema.safeParse({
      ...validInput,
      dataSource: { id: "ds-1" },
    });
    expect(result.success).toBe(false);
  });

  describe("dataSource.id format from the affiliate cloud provider", () => {
    const withFormat = (datasource_id_format: string, id: string) => ({
      ...validInput,
      affiliate: { ...validInput.affiliate, cloud_provider: { datasource_id_format } },
      dataSource: { ...validInput.dataSource, id },
    });

    it("accepts an id matching the cloud provider format", () => {
      const result = AddWizardFormSchema.safeParse(withFormat("[0-9]{12}", "123456789012"));
      expect(result.success).toBe(true);
    });

    it("rejects an id not matching the format and reports it on dataSource.id", () => {
      const result = AddWizardFormSchema.safeParse(withFormat("[0-9]{12}", "not-an-aws-id"));
      expect(result.success).toBe(false);
      expect(result.error?.issues).toEqual([
        expect.objectContaining({ code: "custom", path: ["dataSource", "id"] }),
      ]);
    });

    it("requires the whole id to match, not just a substring", () => {
      const result = AddWizardFormSchema.safeParse(withFormat("[0-9]{12}", "x123456789012x"));
      expect(result.success).toBe(false);
    });

    it("skips the format check when the affiliate has no cloud provider", () => {
      const result = AddWizardFormSchema.safeParse({
        ...validInput,
        affiliate: { ...validInput.affiliate, cloud_provider: null },
      });
      expect(result.success).toBe(true);
    });

    it("skips the format check when the pattern is malformed", () => {
      const result = AddWizardFormSchema.safeParse(withFormat("([unclosed", "anything"));
      expect(result.success).toBe(true);
    });

    it("keeps cloud_provider in the parsed output", () => {
      const result = AddWizardFormSchema.parse(withFormat(".+", "ds-1"));
      expect(result.affiliate.cloud_provider).toEqual({ datasource_id_format: ".+" });
    });
  });

  describe("toDatasourceIdRegExp", () => {
    it("returns null for an empty pattern", () => {
      expect(toDatasourceIdRegExp(undefined)).toBeNull();
      expect(toDatasourceIdRegExp("")).toBeNull();
    });

    it("anchors patterns that are already anchored without breaking them", () => {
      expect(toDatasourceIdRegExp("^[a-z]+$")?.test("abc")).toBe(true);
    });

    it("full-matches alternations", () => {
      const regex = toDatasourceIdRegExp("abc|def");
      expect(regex?.test("abc")).toBe(true);
      expect(regex?.test("abcdef")).toBe(false);
    });
  });
});
