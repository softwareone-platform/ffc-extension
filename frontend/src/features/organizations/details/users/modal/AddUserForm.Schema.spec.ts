import { AddUserFormSchema } from "./AddUserForm.Schema";

describe("AddUserFormSchema", () => {
  const validInput = { email: "user@example.com", display_name: "User" };

  it("accepts a valid payload", () => {
    expect(AddUserFormSchema.safeParse(validInput).success).toBe(true);
  });

  it("rejects an invalid email", () => {
    const result = AddUserFormSchema.safeParse({ ...validInput, email: "not-an-email" });
    expect(result.success).toBe(false);
  });

  it("rejects an empty display_name", () => {
    const result = AddUserFormSchema.safeParse({ ...validInput, display_name: "" });
    expect(result.success).toBe(false);
  });

  it("rejects a whitespace-only display_name once trimmed", () => {
    const result = AddUserFormSchema.safeParse({ ...validInput, display_name: "   " });
    expect(result.success).toBe(false);
  });

  it("rejects a display_name longer than 255 characters", () => {
    const result = AddUserFormSchema.safeParse({
      ...validInput,
      display_name: "a".repeat(256),
    });
    expect(result.success).toBe(false);
  });
});
