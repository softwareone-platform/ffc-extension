import { renderHook } from "@testing-library/react";

import type { DatasourceType } from "~api/ffc-api-model";
import type { DatasourceAction } from "~features/organizations/api/model";
import type { ActionsByRole } from "~shared/hooks/useActionsByRole";
import { makeDatasource } from "~test-utils";

import { useActionOptions } from "./useActionOptions";

const mockFilterActionsByRole = jest.fn() as jest.MockedFunction<ActionsByRole<DatasourceAction>>;

jest.mock("~shared/hooks/useActionsByRole", () => ({
  useActionsByRole: () => mockFilterActionsByRole,
}));

describe("useActionOptions (data-sources)", () => {
  beforeEach(() => {
    mockFilterActionsByRole.mockImplementation((actions) => actions);
  });

  it("returns a force_import action for CNR datasources with isDisabled=false", () => {
    const { result } = renderHook(() => useActionOptions());
    const item = makeDatasource({ type: "aws_cnr" });

    const [action] = result.current(item);

    expect(action).toMatchObject({
      value: "force_import",
      label: "force_import",
      isDisabled: false,
      requiredRoles: ["admin"],
    });
  });

  it.each<DatasourceType>(["azure_tenant", "gcp_tenant", "unknown"])(
    "disables force_import for datasource type '%s'",
    (type) => {
      const { result } = renderHook(() => useActionOptions());
      const item = makeDatasource({ type });

      expect(result.current(item)[0]).toMatchObject({ isDisabled: true });
    },
  );

  it("forwards the built actions to filterActionsByRole and returns its result", () => {
    const filtered = [{ value: "force_import" as const, label: "force_import" }];
    mockFilterActionsByRole.mockReturnValueOnce(filtered);
    const { result } = renderHook(() => useActionOptions());
    const item = makeDatasource({ type: "aws_cnr" });

    const options = result.current(item);

    expect(mockFilterActionsByRole).toHaveBeenCalledWith([
      expect.objectContaining({ value: "force_import", requiredRoles: ["admin"] }),
    ]);
    expect(options).toBe(filtered);
  });
});
