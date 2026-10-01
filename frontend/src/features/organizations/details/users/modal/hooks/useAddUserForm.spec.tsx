import { renderHook } from "@testing-library/react";

import { useAddUserForm } from "./useAddUserForm";

describe("useAddUserForm", () => {
  it("seeds defaultValues from the initial data", () => {
    const { result } = renderHook(() =>
      useAddUserForm({ email: "user@example.com", display_name: "User" }),
    );

    expect(result.current.getValues()).toEqual({
      email: "user@example.com",
      display_name: "User",
    });
  });

  it("initialises formState with no errors on valid defaults", () => {
    const { result } = renderHook(() =>
      useAddUserForm({ email: "user@example.com", display_name: "User" }),
    );

    expect(result.current.formState.errors).toEqual({});
  });
});
