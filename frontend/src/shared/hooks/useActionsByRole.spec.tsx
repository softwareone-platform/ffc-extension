import { renderHook } from "@testing-library/react";

import { mockUserRoleModule, mockUseUserRole } from "~test-utils/mocks/userRole";

import { useActionsByRole, type RoleAwareAction } from "./useActionsByRole";

jest.mock("~shared/hooks/useUserRole", () => mockUserRoleModule);

describe("useActionsByRole", () => {
  beforeEach(() => {
    mockUseUserRole.mockReset();
  });

  it("returns no actions when the role is missing", () => {
    mockUseUserRole.mockReturnValue({ user: null, role: undefined });

    const { result } = renderHook(() => useActionsByRole<"edit" | "delete">());

    expect(result.current([{ value: "edit", label: "Edit" }])).toEqual([]);
  });

  it("returns actions that do not require a role and actions allowed for the current role", () => {
    mockUseUserRole.mockReturnValue({ user: null, role: "admin" });

    const { result } = renderHook(() => useActionsByRole<"edit" | "delete">());
    const actions: RoleAwareAction<"edit" | "delete">[] = [
      { value: "edit", label: "Edit" },
      { value: "delete", label: "Delete", requiredRoles: ["admin"] },
      { value: "delete", label: "Delete for ops", requiredRoles: ["operations"] },
    ];

    expect(result.current(actions)).toEqual([actions[0], actions[1]]);
  });
});

