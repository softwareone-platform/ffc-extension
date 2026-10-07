import { renderHook } from "@testing-library/react";

import { useEditOrganizationForm } from "./useEditOrganizationForm";

describe("useEditOrganizationForm", () => {
  it("seeds defaultValues from the initial data", () => {
    const { result } = renderHook(() =>
      useEditOrganizationForm({
        name: "Acme",
        operations_external_id: "op-1",
        currency: "USD",
      }),
    );

    expect(result.current.getValues()).toEqual({
      name: "Acme",
      operations_external_id: "op-1",
      currency: "USD",
    });
  });
});
