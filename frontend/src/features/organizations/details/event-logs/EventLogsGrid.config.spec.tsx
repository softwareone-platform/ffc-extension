import { renderHook } from "@testing-library/react";

import {
  type GridInfoDialogConfig,
  mockUseAsyncOptions,
  mockUseColumns,
  mockUseFields,
  mockUseGridAsync,
  mockUseGridIdentity,
  mockUseGridInfoDialogConfiguration,
  mockUseViews,
} from "./EventLogsGrid.config.spec.mocks";

import { useGridConfig } from "./EventLogsGrid.config";
import type { useColumns } from "./hooks/useColumns";
import type { useFields } from "./hooks/useFields";
import type { useViews } from "./hooks/useViews";

const columns = [{ name: "time" }] as unknown as ReturnType<typeof useColumns>;
const fields = [{ name: "time", title: "time" }] as ReturnType<typeof useFields>;
const views = [{ name: "logInfo" }] as unknown as ReturnType<typeof useViews>;
const silentRefresh = jest.fn();
const refresh = jest.fn();

function getLatestGridAsyncArg() {
  return mockUseGridAsync.mock.lastCall![0];
}

describe("useGridConfig (organization event logs)", () => {
  beforeEach(() => {
    mockUseColumns.mockReturnValue(columns);
    mockUseFields.mockReturnValue(fields);
    mockUseViews.mockReturnValue(views);
    mockUseAsyncOptions.mockReturnValue({ silentRefresh, refresh, onConfigChange: jest.fn() });
    mockUseGridInfoDialogConfiguration.mockReturnValue({
      noDataConfiguration: {},
    } as GridInfoDialogConfig);
    mockUseGridAsync.mockReturnValue({ onEvent: jest.fn() });
  });

  it("loads async options for the given organization", () => {
    renderHook(() => useGridConfig("org-123"));

    expect(mockUseAsyncOptions).toHaveBeenCalledWith("org-123");
  });

  it("uses a grid identity distinct from the users grid", () => {
    renderHook(() => useGridConfig("org-123"));

    expect(mockUseGridIdentity).toHaveBeenCalledWith("organizations-details-logs");
  });

  it("builds the grid from columns, fields, views, async options and info-dialog config", () => {
    renderHook(() => useGridConfig("org-123"));

    expect(getLatestGridAsyncArg()).toEqual(
      expect.objectContaining({
        id: "organizations-details-logs",
        columns,
        fields,
        views,
        isDefaultView: true,
        selectedView: "default",
        silentRefresh,
        refresh,
        noDataConfiguration: {},
      }),
    );
  });

  it("exposes silentRefresh and refresh alongside the useGridAsync result", () => {
    const onEvent = jest.fn();
    mockUseGridAsync.mockReturnValue({ onEvent });

    const { result } = renderHook(() => useGridConfig("org-123"));

    expect(result.current).toEqual(expect.objectContaining({ silentRefresh, refresh, onEvent }));
  });
});
