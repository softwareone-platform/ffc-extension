import { renderHook, screen } from "@testing-library/react";

import { NO_VALUE } from "@swo/design-system/utils";

import type { DatasourceDiscoveryItem } from "~api/ffc-api-model";
import type { useGridInfoDialogConfiguration } from "~shared/hooks/useGridInfoDialogConfiguration";
import { columnByName, renderColumnCell } from "~test-utils";

import {
  mockStatus,
  mockUseGridIdentity,
  mockUseGridInfoDialogConfiguration,
  mockUseGridInMemory,
} from "./DiscoveryGrid.config.spec.mocks";

import { useColumns, useGridConfig } from "./DiscoveryGrid.config";

const COLUMN_FIELDS = [
  ["resource_type", ["resource_type"]],
  ["last_discovery_at", ["last_discovery_at"]],
  ["status", ["status"]],
] as const;

function makeDiscoveryItem(overrides: Partial<DatasourceDiscoveryItem> = {}) {
  return {
    resource_type: "instance",
    last_discovery_at: "2026-01-15T10:00:00Z",
    status: "completed",
    ...overrides,
  } satisfies DatasourceDiscoveryItem;
}

function getColumns() {
  return renderHook(() => useColumns()).result.current;
}

describe("DiscoveryGrid.config", () => {
  describe("useColumns", () => {
    it("returns columns in fixed order", () => {
      expect(getColumns().map((c) => c.name)).toEqual(COLUMN_FIELDS.map(([name]) => name));
    });

    it.each(COLUMN_FIELDS)("column '%s' maps to fields %j", (name, expectedFields) => {
      expect(columnByName(getColumns(), name).fields).toEqual(expectedFields);
    });

    it("renders the translated resource type", () => {
      renderColumnCell(getColumns(), "resource_type", makeDiscoveryItem());

      expect(screen.getByTestId("grid-cell-simple")).toHaveTextContent("instance");
    });

    it("renders an unknown resource type when it is missing", () => {
      renderColumnCell(getColumns(), "resource_type", makeDiscoveryItem({ resource_type: null }));

      expect(screen.getByTestId("grid-cell-simple")).toHaveTextContent("unknown");
    });

    it("renders the last discovery date", () => {
      renderColumnCell(getColumns(), "last_discovery_at", makeDiscoveryItem());

      expect(screen.getByTestId("grid-cell-date")).toHaveTextContent("2026-01-15T10:00:00Z");
    });

    it.each([
      ["missing", null],
      ["the epoch", "1970-01-01T00:00:00Z"],
    ])("renders NO_VALUE when the last discovery date is %s", (_, lastDiscoveryAt) => {
      renderColumnCell(
        getColumns(),
        "last_discovery_at",
        makeDiscoveryItem({ last_discovery_at: lastDiscoveryAt }),
      );

      expect(screen.queryByTestId("grid-cell-date")).not.toBeInTheDocument();
      expect(screen.getByTestId("grid-cell-simple")).toHaveTextContent(NO_VALUE);
    });

    it("renders the discovery status chip", () => {
      renderColumnCell(getColumns(), "status", makeDiscoveryItem({ status: "failed" }));

      expect(mockStatus).toHaveBeenCalledWith({ status: "failed" });
    });
  });

  describe("useGridConfig", () => {
    beforeEach(() => {
      mockUseGridInfoDialogConfiguration.mockReturnValue({
        noDataConfiguration: {},
      } as ReturnType<typeof useGridInfoDialogConfiguration>);
      mockUseGridInMemory.mockReturnValue({ columns: [] });
    });

    it("builds an in-memory grid over the discovery items with the toolbar and footer hidden", () => {
      const data = [makeDiscoveryItem()];

      renderHook(() => useGridConfig(data));

      expect(mockUseGridIdentity).toHaveBeenCalledWith("datasource-discovery-details");
      expect(mockUseGridInMemory).toHaveBeenCalledWith(
        data,
        expect.objectContaining({
          id: "datasource-discovery-details",
          isDefaultView: true,
          isToHideToolbar: true,
          selectedView: "default",
          isToHideFooter: true,
          noDataConfiguration: {},
        }),
      );
    });

    it("sizes the page to fit every discovery item", () => {
      const data = [makeDiscoveryItem(), makeDiscoveryItem({ resource_type: "volume" })];

      renderHook(() => useGridConfig(data));

      expect(mockUseGridInMemory.mock.lastCall![1]).toMatchObject({ paging: { pageSize: 2 } });
    });

    it("resizes the page when the discovery items change", () => {
      const { rerender } = renderHook(({ data }) => useGridConfig(data), {
        initialProps: { data: [makeDiscoveryItem()] },
      });

      rerender({ data: [makeDiscoveryItem(), makeDiscoveryItem(), makeDiscoveryItem()] });

      expect(mockUseGridInMemory.mock.lastCall![1]).toMatchObject({ paging: { pageSize: 3 } });
    });

    it("returns the in-memory grid props", () => {
      const { result } = renderHook(() => useGridConfig([]));

      expect(result.current).toEqual({ columns: [] });
    });
  });
});
