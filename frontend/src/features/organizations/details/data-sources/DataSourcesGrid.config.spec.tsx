import { renderHook, screen } from "@testing-library/react";

import type { GridEvents, GridFieldDefinition } from "@swo/design-system/grid";
import { NO_VALUE } from "@swo/design-system/utils";

import type { AccountType, DatasourceType, OrganizationRead } from "~api/ffc-api-model";
import type { useGridInfoDialogConfiguration } from "~shared/hooks/useGridInfoDialogConfiguration";
import { mapAxiosResponseDataList } from "~shared/utils/mapAxiosResponseDataList";
import { columnByName, makeDatasource, renderColumnCell } from "~test-utils";

import {
  mockGetActions,
  mockListOrganizationDataSources,
  mockUseGridAsync,
  mockUseGridInfoDialogConfiguration,
  mockUseOrganizationContext,
  mockUseReactQueryRqlGrid,
  mockUseUserRole,
} from "./DataSourcesGrid.config.spec.mocks";

import { useAsyncOptions, useColumns, useFields, useGridConfig } from "./DataSourcesGrid.config";

const COLUMN_FIELDS = [
  ["id", ["id"]],
  ["name", ["name", "datasource_id"]],
  ["type", ["type"]],
  ["parent_id", ["parent_id", "parent.id", "parent.name", "parent.type"]],
  ["resources_charged_this_month", ["resources_charged_this_month"]],
  ["expenses_so_far_this_month", ["expenses_so_far_this_month"]],
  ["expenses_forecast_this_month", ["expenses_forecast_this_month"]],
  ["last_import_at", ["last_import_at"]],
  ["actions", []],
] as const;

function getColumns() {
  return renderHook(() => useColumns()).result.current;
}

function getFields() {
  return renderHook(() => useFields()).result.current;
}

function getLatestOptionsFactory() {
  return mockUseReactQueryRqlGrid.mock.lastCall![1];
}

function getLatestGridAsyncArg() {
  return mockUseGridAsync.mock.lastCall![0];
}

describe("DataSourcesGrid.config", () => {
  beforeEach(() => {
    mockUseOrganizationContext.mockReturnValue({ currency: "USD" } as OrganizationRead);
    mockUseUserRole.mockReturnValue({ user: null, role: "admin" });
    mockUseGridInfoDialogConfiguration.mockReturnValue({
      noDataConfiguration: {},
    } as ReturnType<typeof useGridInfoDialogConfiguration>);
  });

  describe("useColumns", () => {
    it("returns columns in fixed order", () => {
      const columns = getColumns();

      expect(columns.map((c) => c.name)).toEqual(COLUMN_FIELDS.map(([name]) => name));
    });

    it.each(COLUMN_FIELDS)("column '%s' maps to fields %j", (name, expectedFields) => {
      const column = columnByName(getColumns(), name);

      expect(column.fields).toEqual(expectedFields);
    });

    it("marks the id column as hidden", () => {
      const idColumn = columnByName(getColumns(), "id");

      expect(idColumn.isHidden).toBe(true);
    });

    it.each<[AccountType, boolean]>([
      ["operations", true],
      ["admin", false],
    ])("sets the actions column visibility for role '%s'", (role, isHidden) => {
      mockUseUserRole.mockReturnValue({ user: null, role });
      const actionsColumn = columnByName(getColumns(), "actions");

      expect(actionsColumn.isHidden).toBe(isHidden);
    });

    it("renders the name column with EntityReferenceCell showing name, datasource_id and type icon", () => {
      const columns = getColumns();
      const item = makeDatasource();

      renderColumnCell(columns, "name", item);

      expect(screen.getByTestId("primary")).toHaveTextContent("AWS Prod");
      expect(screen.getByTestId("secondary")).toHaveTextContent("aws-prod-123");
      expect(screen.getByTestId("custom-icon")).toHaveTextContent("aws_cnr");
    });

    it("renders the parent_id column with parent details when parent is set", () => {
      const columns = getColumns();
      const item = makeDatasource({
        parent: {
          id: "p-1",
          name: "Parent DS",
          datasource_id: "parent-ds-123",
          type: "azure_tenant",
        },
      });

      renderColumnCell(columns, "parent_id", item);

      expect(screen.getByTestId("primary")).toHaveTextContent("Parent DS");
      expect(screen.getByTestId("secondary")).toHaveTextContent("parent-ds-123");
      expect(screen.getByTestId("custom-icon")).toHaveTextContent("azure_tenant");
    });

    it("renders the parent_id column with NO_VALUE when parent is missing", () => {
      const columns = getColumns();
      const item = makeDatasource({ parent: null });

      renderColumnCell(columns, "parent_id", item);

      expect(screen.getByTestId("grid-cell-simple")).toHaveTextContent(NO_VALUE);
    });

    it("renders resources_charged_this_month without a currency code when organization context is undefined", () => {
      const columns = getColumns();
      const item = makeDatasource({ resources_charged_this_month: 12 });

      renderColumnCell(columns, "resources_charged_this_month", item);

      expect(screen.getByTestId("grid-cell-currency")).toHaveTextContent("12|");
    });

    it.each([
      ["expenses_so_far_this_month", "expenses_so_far_this_month" as const, 42],
      ["expenses_forecast_this_month", "expenses_forecast_this_month" as const, 55],
    ])("renders %s with currency from organization context", (columnName, field, value) => {
      const columns = getColumns();
      const item = makeDatasource({ [field]: value });

      renderColumnCell(columns, columnName, item);

      expect(screen.getByTestId("grid-cell-currency")).toHaveTextContent(`${value}|USD`);
    });

    it("passes fractional expense values through to GridCellCurrency unchanged", () => {
      const columns = getColumns();
      const item = makeDatasource({ expenses_so_far_this_month: 0.000432 });

      renderColumnCell(columns, "expenses_so_far_this_month", item);

      expect(screen.getByTestId("grid-cell-currency")).toHaveTextContent("0.000432|USD");
    });

    it("renders currency cells without a currency code when organization context is undefined", () => {
      mockUseOrganizationContext.mockReturnValue(undefined);
      const columns = getColumns();
      const item = makeDatasource({ expenses_so_far_this_month: 7 });

      renderColumnCell(columns, "expenses_so_far_this_month", item);

      expect(screen.getByTestId("grid-cell-currency")).toHaveTextContent("7|");
    });

    it.each([
      ["epoch numeric", 0 as unknown as string],
      ["epoch ISO string", "1970-01-01T00:00:00Z"],
      ["undefined", undefined],
    ])("renders last_import_at as NO_VALUE when the value is %s", (_label, value) => {
      const columns = getColumns();
      const item = { ...makeDatasource(), last_import_at: value };

      renderColumnCell(columns, "last_import_at", item);

      expect(screen.getByTestId("grid-cell-simple")).toHaveTextContent(NO_VALUE);
    });

    it("renders last_import_at as a date when the value is real", () => {
      const columns = getColumns();
      const item = makeDatasource({ last_import_at: "2026-01-15T10:00:00Z" });

      renderColumnCell(columns, "last_import_at", item);

      expect(screen.getByTestId("grid-cell-date")).toHaveTextContent("2026-01-15T10:00:00Z");
    });

    it("renders the actions column with dynamic actions for the item", () => {
      mockGetActions.mockReturnValue([{ value: "force_import", label: "Force import" }]);
      const columns = getColumns();
      const item = makeDatasource();

      renderColumnCell(columns, "actions", item);

      expect(screen.getByTestId("actions-item-id")).toHaveTextContent(item.id);
      expect(screen.getByTestId("actions-count")).toHaveTextContent("1");
      expect(mockGetActions).toHaveBeenCalledWith(item);
    });
  });

  describe("useFields", () => {
    it("returns id, name, type and datasource_id fields", () => {
      const fields = getFields();

      expect(fields.map((f) => f.name)).toEqual(["id", "name", "type", "datasource_id"]);
    });

    it("exposes the type field as a list with datasource type options", () => {
      const fields = getFields();
      const typeField = fields.find((f) => f.name === "type") as GridFieldDefinition;

      expect(typeField).toMatchObject({ type: "list" });
      const expectedTypes = [
        "aws_cnr",
        "azure_cnr",
        "azure_tenant",
        "gcp_cnr",
        "gcp_tenant",
        "unknown",
      ] as const satisfies readonly DatasourceType[];
      expect(typeField.options!.map((option) => option.value)).toEqual(expectedTypes);
    });
  });

  describe("useAsyncOptions", () => {
    it("initializes useReactQueryRqlGrid with the OrganizationDataSources base query key", () => {
      renderHook(() => useAsyncOptions("org-123"));

      expect(mockUseReactQueryRqlGrid).toHaveBeenCalledWith(
        ["OrganizationDataSources"],
        expect.any(Function),
      );
    });

    it("builds organization-scoped query options for listing data sources", () => {
      renderHook(() => useAsyncOptions("org-123"));
      const optionsFactory = getLatestOptionsFactory();
      const query = { toString: () => "rql-string" };

      const options = optionsFactory(query);
      options.queryFn();

      expect(options.queryKey).toEqual([["OrganizationDataSources"], "rql-string", "org-123"]);
      expect(mockListOrganizationDataSources).toHaveBeenCalledWith("org-123", query);
    });

    it("wires mapAxiosResponseDataList as the select transform", () => {
      renderHook(() => useAsyncOptions("org-123"));
      const optionsFactory = getLatestOptionsFactory();

      const options = optionsFactory({ toString: () => "rql" });

      expect(options.select).toBe(mapAxiosResponseDataList);
    });

    it("updates the scoped queryKey when organizationId changes", () => {
      const { rerender } = renderHook(({ orgId }) => useAsyncOptions(orgId), {
        initialProps: { orgId: "org-1" },
      });
      const query = { toString: () => "rql" };

      rerender({ orgId: "org-2" });
      const latestFactory = getLatestOptionsFactory();
      const options = latestFactory(query);
      options.queryFn();

      expect(options.queryKey).toEqual([["OrganizationDataSources"], "rql", "org-2"]);
      expect(mockListOrganizationDataSources).toHaveBeenLastCalledWith("org-2", query);
    });
  });

  describe("useGridConfig", () => {
    const silentRefresh = jest.fn();
    const refresh = jest.fn();

    beforeEach(() => {
      mockUseReactQueryRqlGrid.mockReturnValue({
        silentRefresh,
        refresh,
        onConfigChange: jest.fn(),
        data: [],
        total: 0,
      });
    });

    it("wires useColumns, useFields, async options, and info-dialog config into useGridAsync", () => {
      const gridAsyncResult = { onEvent: jest.fn() };
      mockUseGridAsync.mockReturnValue(gridAsyncResult);

      renderHook(() => useGridConfig("org-123"));

      const arg = getLatestGridAsyncArg();
      expect(arg).toEqual(
        expect.objectContaining({
          id: "ffc-extension__organizations-details-data-sources--admin",
          memoizeId: "ffc-extension__organizations-details-data-sources--admin",
          storageParameters: ["unknown"],
          isDefaultView: true,
          selectedView: "default",
          silentRefresh,
          noDataConfiguration: expect.any(Object),
          onEvent: expect.any(Function),
        }),
      );
      expect(arg.columns).toHaveLength(COLUMN_FIELDS.length);
      expect(arg.fields).toHaveLength(4);
    });

    it("exposes silentRefresh and refresh alongside the useGridAsync result", () => {
      const gridAsyncResult = { onEvent: jest.fn(), someProp: 1 };
      mockUseGridAsync.mockReturnValue(gridAsyncResult);

      const { result } = renderHook(() => useGridConfig("org-123"));

      expect(result.current.silentRefresh).toBe(silentRefresh);
      expect(result.current.refresh).toBe(refresh);
      expect(result.current.onEvent).toBe(gridAsyncResult.onEvent);
    });

    it("forwards RowActionTriggered events to onAction with the action, item, and silentRefresh", () => {
      mockUseGridAsync.mockReturnValue({});
      const onAction = jest.fn();

      renderHook(() => useGridConfig("org-123", onAction));
      const onEvent = getLatestGridAsyncArg().onEvent!;
      const item = { id: "ds-1" };

      onEvent({ type: "RowActionTriggered", data: { action: "force_import", item } });

      expect(onAction).toHaveBeenCalledWith("force_import", item, silentRefresh);
    });

    it("ignores events that are not RowActionTriggered", () => {
      mockUseGridAsync.mockReturnValue({});
      const onAction = jest.fn();

      renderHook(() => useGridConfig("org-123", onAction));
      const onEvent = getLatestGridAsyncArg().onEvent!;

      onEvent({ type: "SomeOtherEvent", data: {} } as unknown as GridEvents);

      expect(onAction).not.toHaveBeenCalled();
    });

    it("does not throw when a row action is triggered without an onAction handler", () => {
      mockUseGridAsync.mockReturnValue({});

      renderHook(() => useGridConfig("org-123"));
      const onEvent = getLatestGridAsyncArg().onEvent!;

      expect(() =>
        onEvent({
          type: "RowActionTriggered",
          data: { action: "force_import", item: { id: "ds-1" } },
        }),
      ).not.toThrow();
    });
  });
});
