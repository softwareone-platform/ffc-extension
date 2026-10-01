import { EditOrganizationFormSchema } from "./EditOrganization.Schema";

describe("EditOrganizationFormSchema", () => {
  const validInput = {
    name: "Acme",
    operations_external_id: "op-1",
    currency: "USD",
  };

  it("accepts a valid payload", () => {
    expect(EditOrganizationFormSchema.safeParse(validInput).success).toBe(true);
  });

  it.each(["name", "operations_external_id", "currency"] as const)(
    "rejects an empty %s",
    (field) => {
      const result = EditOrganizationFormSchema.safeParse({ ...validInput, [field]: "" });
      expect(result.success).toBe(false);
    },
  );

  it("rejects a whitespace-only name once trimmed", () => {
    const result = EditOrganizationFormSchema.safeParse({ ...validInput, name: "   " });
    expect(result.success).toBe(false);
  });

  it("rejects a currency longer than 5 characters", () => {
    const result = EditOrganizationFormSchema.safeParse({ ...validInput, currency: "TOOLONG" });
    expect(result.success).toBe(false);
  });

  it("rejects a name longer than 255 characters", () => {
    const result = EditOrganizationFormSchema.safeParse({
      ...validInput,
      name: "a".repeat(256),
    });
    expect(result.success).toBe(false);
  });
});
