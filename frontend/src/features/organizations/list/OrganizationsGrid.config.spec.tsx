import { renderHook } from "@testing-library/react";

import type { GridEvents } from "@swo/design-system/grid";

import type { useGridInfoDialogConfiguration } from "~shared/hooks/useGridInfoDialogConfiguration";

import {
  mockUseAsyncOptions,
  mockUseColumns,
  mockUseFields,
  mockUseGridAsync,
  mockUseGridInfoDialogConfiguration,
  mockUseUserRole,
  mockUseViews,
} from "./OrganizationsGrid.config.spec.mocks";

import { useGridConfig } from "./OrganizationsGrid.config";

describe("useGridConfig (organizations list)", () => {
  const silentRefresh = jest.fn();
  const refresh = jest.fn();

  beforeEach(() => {
    mockUseUserRole.mockReturnValue({ user: null, role: "admin" });
    mockUseColumns.mockReturnValue([{ name: "name", fields: ["name"] }]);
    mockUseFields.mockReturnValue([{ name: "id", title: "id" }]);
    mockUseViews.mockReturnValue([{ name: "main", title: "main", configuration: {} }]);
    mockUseAsyncOptions.mockReturnValue({ silentRefresh, refresh });
    mockUseGridInfoDialogConfiguration.mockReturnValue({
      noDataConfiguration: {},
    } as ReturnType<typeof useGridInfoDialogConfiguration>);
  });

  it("wires columns, fields, views, async options, and info-dialog config into useGridAsync", () => {
    mockUseGridAsync.mockReturnValue({});

    renderHook(() => useGridConfig());

    const arg = mockUseGridAsync.mock.lastCall![0];
    expect(arg).toEqual(
      expect.objectContaining({
        isDefaultView: false,
        selectedView: "main",
        silentRefresh,
        noDataConfiguration: expect.any(Object),
        onEvent: expect.any(Function),
      }),
    );
    expect(arg.columns).toHaveLength(1);
    expect(arg.fields).toHaveLength(1);
    expect(arg.views).toHaveLength(1);
  });

  it("exposes refresh and silentRefresh alongside the useGridAsync result", () => {
    mockUseGridAsync.mockReturnValue({ onEvent: jest.fn(), extra: 42 });

    const { result } = renderHook(() => useGridConfig());

    expect(result.current.refresh).toBe(refresh);
    expect(result.current.silentRefresh).toBe(silentRefresh);
  });

  it("forwards RowActionTriggered events to onAction with action, item, and silentRefresh", () => {
    mockUseGridAsync.mockReturnValue({});
    const onAction = jest.fn();

    renderHook(() => useGridConfig(onAction));
    const onEvent = mockUseGridAsync.mock.lastCall![0].onEvent!;

    onEvent({ type: "RowActionTriggered", data: { action: "edit", item: { id: "o-1" } } });

    expect(onAction).toHaveBeenCalledWith("edit", { id: "o-1" }, silentRefresh);
  });

  it("ignores events that are not RowActionTriggered", () => {
    mockUseGridAsync.mockReturnValue({});
    const onAction = jest.fn();

    renderHook(() => useGridConfig(onAction));
    const onEvent = mockUseGridAsync.mock.lastCall![0].onEvent!;

    onEvent({ type: "SomeOtherEvent", data: {} } as unknown as GridEvents);

    expect(onAction).not.toHaveBeenCalled();
  });

  it("safely no-ops on RowActionTriggered when no onAction is provided", () => {
    mockUseGridAsync.mockReturnValue({});

    renderHook(() => useGridConfig());
    const onEvent = mockUseGridAsync.mock.lastCall![0].onEvent!;

    expect(() =>
      onEvent({ type: "RowActionTriggered", data: { action: "edit", item: { id: "o-1" } } }),
    ).not.toThrow();
  });
});
