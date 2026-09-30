import type { PropsWithChildren } from "react";

import { renderHook } from "@testing-library/react";

import type { Me } from "~api/ffc-api-model";
import { UserContext } from "~shared/providers/UserContext";

import { useUserRole } from "./useUserRole";

describe("useUserRole", () => {
  it("returns undefined user and role when no provider value exists", () => {
    const { result } = renderHook(() => useUserRole());

    expect(result.current.user).toBeUndefined();
    expect(result.current.role).toBeUndefined();
  });

  it("returns the context user and the derived account role", () => {
    const user = {
      account: { type: "admin" },
    } as Me;
    const wrapper = ({ children }: PropsWithChildren) => (
      <UserContext.Provider value={user}>{children}</UserContext.Provider>
    );

    const { result } = renderHook(() => useUserRole(), { wrapper });

    expect(result.current.user).toBe(user);
    expect(result.current.role).toBe("admin");
  });
});
