import { renderHook } from "@testing-library/react";

import { useDefaultInfoDialogConfiguration } from "@swo/design-system/grid";

import { mockFixedT } from "~test-utils/mocks/fixedT";

import { useFixedT } from "./useFixedT";
import { useGridInfoDialogConfiguration } from "./useGridInfoDialogConfiguration";

jest.mock("@swo/design-system/grid", () => ({
  useDefaultInfoDialogConfiguration: jest.fn(),
}));

jest.mock("./useFixedT", () => ({
  useFixedT: jest.fn(),
}));

describe("useGridInfoDialogConfiguration", () => {
  it("merges the default no-data configuration with translated content", () => {
    jest.mocked(useDefaultInfoDialogConfiguration).mockReturnValue({
      defaultNoDataConfiguration: {
        title: "Default title",
      },
    } as never);
    mockFixedT(jest.mocked(useFixedT), (key) => `t:${key}`);

    const { result } = renderHook(() => useGridInfoDialogConfiguration());

    expect(result.current.noDataConfiguration).toEqual({
      title: "Default title",
      description: "t:infoDialog:noData:description",
      button: undefined,
    });
  });
});
