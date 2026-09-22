import { renderHook } from "@testing-library/react";

import type { GridFieldDefinition } from "@swo/design-system/grid";

import { NO_VALUE } from "@swo/design-system/utils";

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

import {
  useAsyncOptions,
  useColumns,
  useFields,
  useGridConfig,
} from "./DataSourcesGrid.config";

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

describe("DataSourcesGrid.config", () => {
  beforeEach(() => {
    mockUseOrganizationContext.mockReturnValue({ currency: "USD" });
    mockUseUserRole.mockReturnValue({ user: null, role: "admin" });
    mockUseGridInfoDialogConfiguration.mockReturnValue({ noDataConfiguration: {} });
  });

  describe("useColumns", () => {
    it("returns columns in the expected order", () => {
      const { result } = renderHook(() => useColumns());

      expect(result.current.map((c) => c.name)).toEqual(COLUMN_FIELDS.map(([name]) => name));
    });

    it.each(COLUMN_FIELDS)("column '%s' maps to fields %j", (name, expectedFields) => {
      const { result } = renderHook(() => useColumns());
      const column = columnByName(result.current, name);

      expect(column.fields).toEqual(expectedFields);
    });

    it("marks the id column as hidden", () => {
      const { result } = renderHook(() => useColumns());
      const idColumn = columnByName(result.current, "id");

      expect(idColumn.isHidden).toBe(true);
    });

    it.each([
      ["operations", true],
      ["admin", false],
    ])("hides the actions column for role '%s' → isHidden=%s", (role, isHidden) => {
      mockUseUserRole.mockReturnValue({ user: null, role });
      const { result } = renderHook(() => useColumns());
      const actionsColumn = columnByName(result.current, "actions");

      expect(actionsColumn.isHidden).toBe(isHidden);
    });

    it("renders the name column with EntityReferenceCell showing name, datasource_id and type icon", () => {
      const { result } = renderHook(() => useColumns());
      const item = makeDatasource();

      const { getByTestId } = renderColumnCell(result.current, "name", item);

      expect(getByTestId("primary")).toHaveTextContent("AWS Prod");
      expect(getByTestId("secondary")).toHaveTextContent("aws-prod-123");
      expect(getByTestId("custom-icon")).toHaveTextContent("aws_cnr");
    });

    it("renders the parent_id column with parent details when parent is set", () => {
      const { result } = renderHook(() => useColumns());
      const item = makeDatasource({
        parent: {
          id: "p-1",
          name: "Parent DS",
          datasource_id: "parent-ds-123",
          type: "azure_tenant",
        },
      });

      const { getByTestId } = renderColumnCell(result.current, "parent_id", item);

      expect(getByTestId("primary")).toHaveTextContent("Parent DS");
      expect(getByTestId("secondary")).toHaveTextContent("parent-ds-123");
      expect(getByTestId("custom-icon")).toHaveTextContent("azure_tenant");
    });

    it("renders the parent_id column with NO_VALUE when parent is missing", () => {
      const { result } = renderHook(() => useColumns());
      const item = makeDatasource({ parent: null });

      const { getByTestId } = renderColumnCell(result.current, "parent_id", item);

      expect(getByTestId("grid-cell-simple")).toHaveTextContent(NO_VALUE);
    });

    it("renders resources_charged_this_month with empty currency", () => {
      const { result } = renderHook(() => useColumns());
      const item = makeDatasource({ resources_charged_this_month: 12 });

      const { getByTestId } = renderColumnCell(
        result.current,
        "resources_charged_this_month",
        item,
      );

      expect(getByTestId("grid-cell-currency")).toHaveTextContent("12|");
    });

    it.each([
      ["expenses_so_far_this_month", "expenses_so_far_this_month" as const, 42],
      ["expenses_forecast_this_month", "expenses_forecast_this_month" as const, 55],
    ])("renders %s with currency from organization context", (columnName, field, value) => {
      const { result } = renderHook(() => useColumns());
      const item = makeDatasource({ [field]: value });

      const { getByTestId } = renderColumnCell(result.current, columnName, item);

      expect(getByTestId("grid-cell-currency")).toHaveTextContent(`${value}|USD`);
    });

    it("passes fractional expense values through to GridCellCurrency unchanged", () => {
      const { result } = renderHook(() => useColumns());
      const item = makeDatasource({ expenses_so_far_this_month: 0.000432 });

      const { getByTestId } = renderColumnCell(
        result.current,
        "expenses_so_far_this_month",
        item,
      );

      expect(getByTestId("grid-cell-currency")).toHaveTextContent("0.000432|USD");
    });

    it("falls back to empty currency when organization context is undefined", () => {
      mockUseOrganizationContext.mockReturnValue(undefined);
      const { result } = renderHook(() => useColumns());
      const item = makeDatasource({ expenses_so_far_this_month: 7 });

      const { getByTestId } = renderColumnCell(
        result.current,
        "expenses_so_far_this_month",
        item,
      );

      expect(getByTestId("grid-cell-currency")).toHaveTextContent("7|");
    });

    it.each([
      ["epoch numeric", 0 as unknown as string],
      ["epoch ISO string", "1970-01-01T00:00:00Z"],
      ["undefined", undefined],
    ])("renders last_import_at as NO_VALUE when the value is %s", (_label, value) => {
      const { result } = renderHook(() => useColumns());
      const item = { ...makeDatasource(), last_import_at: value };

      const { getByTestId } = renderColumnCell(result.current, "last_import_at", item);

      expect(getByTestId("grid-cell-simple")).toHaveTextContent(NO_VALUE);
    });

    it("renders last_import_at as a date when the value is real", () => {
      const { result } = renderHook(() => useColumns());
      const item = makeDatasource({ last_import_at: "2026-01-15T10:00:00Z" });

      const { getByTestId } = renderColumnCell(result.current, "last_import_at", item);

      expect(getByTestId("grid-cell-date")).toHaveTextContent("2026-01-15T10:00:00Z");
    });

    it("renders the actions column with dynamic actions for the item", () => {
      mockGetActions.mockReturnValue([{ value: "force_import", label: "Force import" }]);
      const { result } = renderHook(() => useColumns());
      const item = makeDatasource();

      const { getByTestId } = renderColumnCell(result.current, "actions", item);

      expect(getByTestId("actions-item-id")).toHaveTextContent(item.id);
      expect(getByTestId("actions-count")).toHaveTextContent("1");
      expect(mockGetActions).toHaveBeenCalledWith(item);
    });
  });

  describe("useFields", () => {
    it("returns id, name, type and datasource_id fields", () => {
      const { result } = renderHook(() => useFields());

      expect(result.current.map((f) => f.name)).toEqual([
        "id",
        "name",
        "type",
        "datasource_id",
      ]);
    });

    it("exposes the type field as a list with datasource type options", () => {
      const { result } = renderHook(() => useFields());
      const typeField = result.current.find((f) => f.name === "type") as GridFieldDefinition;

      expect(typeField).toMatchObject({ type: "list" });
      expect(typeField.options!.map((option) => option.value)).toEqual([
        "aws_cnr",
        "azure_cnr",
        "azure_tenant",
        "gcp_cnr",
        "gcp_tenant",
        "unknown",
      ]);
    });
  });

  describe("useAsyncOptions", () => {
    it("initialises useReactQueryRqlGrid with the OrganizationDataSources base query key", () => {
      renderHook(() => useAsyncOptions("org-123"));

      expect(mockUseReactQueryRqlGrid).toHaveBeenCalledWith(
        ["OrganizationDataSources"],
        expect.any(Function),
      );
    });

    it("builds query options that scope the queryKey by organizationId and delegate to the API", () => {
      renderHook(() => useAsyncOptions("org-123"));
      const optionsFactory = mockUseReactQueryRqlGrid.mock.lastCall![1];
      const query = { toString: () => "rql-string" };

      const options = optionsFactory(query);
      options.queryFn();

      expect(options.queryKey).toEqual([["OrganizationDataSources"], "rql-string", "org-123"]);
      expect(mockListOrganizationDataSources).toHaveBeenCalledWith("org-123", query);
    });

    it("wires mapAxiosResponseDataList as the select transform", () => {
      renderHook(() => useAsyncOptions("org-123"));
      const optionsFactory = mockUseReactQueryRqlGrid.mock.lastCall![1];

      const options = optionsFactory({ toString: () => "rql" });

      expect(options.select).toBe(mapAxiosResponseDataList);
    });

    it("re-scopes the queryKey when organizationId changes", () => {
      const { rerender } = renderHook(({ orgId }) => useAsyncOptions(orgId), {
        initialProps: { orgId: "org-1" },
      });
      const query = { toString: () => "rql" };

      rerender({ orgId: "org-2" });
      const latestFactory = mockUseReactQueryRqlGrid.mock.lastCall![1];
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

    it("passes columns, fields, asyncOptions and gridInfoDialogConfig into useGridAsync", () => {
      const gridAsyncResult = { onEvent: jest.fn() };
      mockUseGridAsync.mockReturnValue(gridAsyncResult);

      renderHook(() => useGridConfig("org-123"));

      const arg = mockUseGridAsync.mock.lastCall![0];
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

    it("invokes onAction with the row's action, item and silentRefresh on RowActionTriggered", () => {
      mockUseGridAsync.mockReturnValue({});
      const onAction = jest.fn();

      renderHook(() => useGridConfig("org-123", onAction));
      const onEvent = mockUseGridAsync.mock.lastCall![0].onEvent;
      const item = { id: "ds-1" };

      onEvent({ type: "RowActionTriggered", data: { action: "force_import", item } });

      expect(onAction).toHaveBeenCalledWith("force_import", item, silentRefresh);
    });

    it("ignores non-RowActionTriggered events", () => {
      mockUseGridAsync.mockReturnValue({});
      const onAction = jest.fn();

      renderHook(() => useGridConfig("org-123", onAction));
      const onEvent = mockUseGridAsync.mock.lastCall![0].onEvent;

      onEvent({ type: "SomeOtherEvent", data: {} });

      expect(onAction).not.toHaveBeenCalled();
    });
  });
});
