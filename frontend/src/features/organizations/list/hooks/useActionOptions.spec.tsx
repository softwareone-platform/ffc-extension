import { renderHook } from "@testing-library/react";

import type { OrganizationStatus } from "~api/ffc-api-model";
import type { OrganizationAction } from "~features/organizations/api/model";
import type { ActionsByRole } from "~shared/hooks/useActionsByRole";
import { makeOrganization } from "~test-utils";

import { useActionOptions } from "./useActionOptions";

const mockFilterActionsByRole = jest.fn() as jest.MockedFunction<ActionsByRole<OrganizationAction>>;

jest.mock("~shared/hooks/useActionsByRole", () => ({
  useActionsByRole: () => mockFilterActionsByRole,
}));

describe("useActionOptions (organizations list)", () => {
  beforeEach(() => {
    mockFilterActionsByRole.mockImplementation((actions) => actions);
  });

  it.each<OrganizationStatus>(["active", "terminated"])(
    "enables edit for status '%s'",
    (status) => {
      const { result } = renderHook(() => useActionOptions());
      const item = makeOrganization({ status });

      const [edit] = result.current(item);

      expect(edit).toMatchObject({
        value: "edit",
        isDisabled: false,
        requiredRoles: ["admin"],
      });
    },
  );

  it.each<OrganizationStatus>(["deleted"])("disables edit for status '%s'", (status) => {
    const { result } = renderHook(() => useActionOptions());
    const item = makeOrganization({ status });

    const [edit] = result.current(item);

    expect(edit).toMatchObject({ isDisabled: true });
  });

  it("enables delete only when the organization is terminated", () => {
    const { result } = renderHook(() => useActionOptions());

    const [, deleteActive] = result.current(makeOrganization({ status: "active" }));
    const [, deleteTerminated] = result.current(makeOrganization({ status: "terminated" }));

    expect(deleteActive).toMatchObject({ isDisabled: true });
    expect(deleteTerminated).toMatchObject({ isDisabled: false });
  });

  it("marks the delete action as dangerous via a className", () => {
    const { result } = renderHook(() => useActionOptions());

    const [, deleteAction] = result.current(makeOrganization({ status: "terminated" }));

    expect(deleteAction).toMatchObject({ props: { className: "dangerous-option" } });
  });

  it("forwards the built actions to filterActionsByRole and returns its result", () => {
    const filtered = [{ value: "edit" as const, label: "edit" }];
    mockFilterActionsByRole.mockReturnValueOnce(filtered);
    const { result } = renderHook(() => useActionOptions());

    const options = result.current(makeOrganization({ status: "active" }));

    expect(mockFilterActionsByRole).toHaveBeenCalledWith([
      expect.objectContaining({ value: "edit", requiredRoles: ["admin"] }),
      expect.objectContaining({ value: "delete", requiredRoles: ["admin"] }),
    ]);
    expect(options).toBe(filtered);
  });
});
