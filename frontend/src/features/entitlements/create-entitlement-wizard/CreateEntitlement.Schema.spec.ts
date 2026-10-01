import { AddWizardFormSchema } from "./CreateEntitlement.Schema";

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
});
