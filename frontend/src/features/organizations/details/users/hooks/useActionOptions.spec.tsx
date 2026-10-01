import { renderHook } from "@testing-library/react";

import type { EmployeeActions } from "~features/organizations/api/model";
import type { ActionsByRole } from "~shared/hooks/useActionsByRole";
import { makeEmployee } from "~test-utils";

import { useActionOptions } from "./useActionOptions";

const mockFilterActionsByRole = jest.fn() as jest.MockedFunction<ActionsByRole<EmployeeActions>>;

jest.mock("~shared/hooks/useActionsByRole", () => ({
  useActionsByRole: () => mockFilterActionsByRole,
}));

describe("useActionOptions (users)", () => {
  beforeEach(() => {
    mockFilterActionsByRole.mockImplementation((actions) => actions);
  });

  it("returns a make_admin action enabled for a non-admin employee", () => {
    const { result } = renderHook(() => useActionOptions());

    const [action] = result.current(makeEmployee({ is_admin: false }));

    expect(action).toMatchObject({
      value: "make_admin",
      label: "make_admin",
      isDisabled: false,
      requiredRoles: ["admin"],
    });
  });

  it("disables the make_admin action for employees that are already admin", () => {
    const { result } = renderHook(() => useActionOptions());

    const [action] = result.current(makeEmployee({ is_admin: true }));

    expect(action).toMatchObject({ isDisabled: true });
  });

  it("forwards the built actions to filterActionsByRole and returns its result", () => {
    const filtered = [{ value: "make_admin" as const, label: "make_admin" }];
    mockFilterActionsByRole.mockReturnValueOnce(filtered);
    const { result } = renderHook(() => useActionOptions());

    const options = result.current(makeEmployee());

    expect(mockFilterActionsByRole).toHaveBeenCalledWith([
      expect.objectContaining({ value: "make_admin", requiredRoles: ["admin"] }),
    ]);
    expect(options).toBe(filtered);
  });
});
