import { renderHook } from "@testing-library/react";

import type { ListItem } from "@swo/design-system/dropdown";

import type { EntitlementStatus } from "~api/ffc-api-model";
import type { EntitlementAction } from "~features/entitlements/api/model";
import { makeEntitlement } from "~test-utils";

import { useActionOptions } from "./useActionOptions";

type ActionItem = ListItem<EntitlementAction>;

function getActions(fn: ReturnType<typeof useActionOptions>, status: EntitlementStatus) {
  const [terminate, , deleteAction] = fn(makeEntitlement({ status })) as unknown as [
    ActionItem,
    unknown,
    ActionItem,
  ];
  return { terminate, deleteAction };
}

describe("useActionOptions (entitlements list)", () => {
  it("returns terminate action, a divider, and delete action in fixed order", () => {
    const { result } = renderHook(() => useActionOptions());

    const options = result.current(makeEntitlement({ status: "active" }));

    expect(options.map((o) => ("type" in o ? "divider" : o.value))).toEqual([
      "terminate",
      "divider",
      "delete",
    ]);
  });

  it("marks both action options with the dangerous-option className", () => {
    const { result } = renderHook(() => useActionOptions());

    const { terminate, deleteAction } = getActions(result.current, "active");

    expect(terminate.props).toMatchObject({ className: "dangerous-option" });
    expect(deleteAction.props).toMatchObject({ className: "dangerous-option" });
  });

  it.each<[EntitlementStatus, boolean]>([
    ["active", false],
    ["new", true],
    ["terminated", true],
    ["deleted", true],
  ])(
    "enables terminate only for status='active' — for '%s' → isDisabled=%s",
    (status, expected) => {
      const { result } = renderHook(() => useActionOptions());

      const { terminate } = getActions(result.current, status);

      expect(terminate.isDisabled).toBe(expected);
    },
  );

  it.each<[EntitlementStatus, boolean]>([
    ["active", true],
    ["new", false],
    ["terminated", true],
    ["deleted", true],
  ])("enables delete only for status='new' — for '%s' → isDisabled=%s", (status, expected) => {
    const { result } = renderHook(() => useActionOptions());

    const { deleteAction } = getActions(result.current, status);

    expect(deleteAction.isDisabled).toBe(expected);
  });
});
