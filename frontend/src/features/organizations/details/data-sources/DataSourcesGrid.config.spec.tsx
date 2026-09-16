import { ReactNode } from "react";

import { render, renderHook } from "@testing-library/react";

import { DatasourceRead } from "~api/ffc-api-model";

import {
  useAsyncOptions,
  useColumns,
  useFields,
  useGridConfig,
} from "./DataSourcesGrid.config";

const NO_VALUE = "—";

const mockUseGridAsync = jest.fn();
jest.mock("@swo/design-system/grid", () => ({
  GridCellSimple: ({ children }: { children: ReactNode }) => (
    <div data-testid="grid-cell-simple">{children}</div>
  ),
  useGridAsync: (config: unknown) => mockUseGridAsync(config),
}));

jest.mock("@swo/design-system/entity-reference-cell", () => ({
  EntityReferenceCell: ({
    primaryContent,
    secondaryContent,
    icon,
  }: {
    primaryContent: ReactNode;
    secondaryContent: ReactNode;
    icon: ReactNode;
  }) => (
    <div data-testid="entity-reference-cell">
      <span data-testid="primary">{primaryContent}</span>
      <span data-testid="secondary">{secondaryContent}</span>
      <span data-testid="icon">{icon}</span>
    </div>
  ),
}));

jest.mock("@swo/design-system/utils", () => ({
  ...jest.requireActual("@swo/design-system/utils"),
  NO_VALUE: "—",
}));

jest.mock("~shared/components/custom-icons/CustomIcon", () => ({
  __esModule: true,
  default: ({ name }: { name: string }) => <div data-testid="custom-icon">{name}</div>,
}));

jest.mock("~shared/components/grid/GridCellCurrency", () => ({
  GridCellCurrency: ({ value, currency }: { value: number; currency: string }) => (
    <div data-testid="grid-cell-currency">{`${value}|${currency}`}</div>
  ),
}));

jest.mock("~shared/components/grid/GridCellDate", () => ({
  GridCellDate: ({ value }: { value: unknown }) => (
    <div data-testid="grid-cell-date">{String(value)}</div>
  ),
}));

jest.mock("~shared/components/grid/GridCellDynamicActions", () => ({
  GridCellDynamicActions: ({ item, actions }: { item: unknown; actions: unknown }) => (
    <div data-testid="grid-cell-dynamic-actions">
      <span data-testid="actions-item-id">{(item as { id?: string }).id}</span>
      <span data-testid="actions-count">
        {Array.isArray(actions) ? actions.length : 0}
      </span>
    </div>
  ),
}));

jest.mock("~shared/utils/DateUtils", () => ({
  isEpoch: (value: unknown) => value === 0 || value === "1970-01-01T00:00:00Z",
}));

const mockUseOrganizationContext = jest.fn();
jest.mock("~organizations/providers/OrganizationsProvider", () => ({
  useOrganizationContext: () => mockUseOrganizationContext(),
}));

const mockListOrganizationDataSources = jest.fn();
jest.mock("~organizations/api", () => ({
  useOrganizationsApi: () => ({
    listOrganizationDataSources: mockListOrganizationDataSources,
  }),
}));

const mockUseReactQueryRqlGrid = jest.fn();
jest.mock("~shared/hooks/useReactQueryRqlGrid", () => ({
  useReactQueryRqlGrid: (...args: unknown[]) => mockUseReactQueryRqlGrid(...args),
}));

const mockUseUserRole = jest.fn();
jest.mock("~shared/hooks/useUserRole", () => ({
  useUserRole: () => mockUseUserRole(),
}));

const mockUseGridInfoDialogConfiguration = jest.fn();
jest.mock("~shared/hooks/useGridInfoDialogConfiguration", () => ({
  useGridInfoDialogConfiguration: () => mockUseGridInfoDialogConfiguration(),
}));

const mockGetActions = jest.fn();
jest.mock("./hooks/useActionOptions", () => ({
  useActionOptions: () => mockGetActions,
}));

describe("DataSourcesGrid.config", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseOrganizationContext.mockReturnValue({ currency: "USD" });
    mockUseUserRole.mockReturnValue({ user: null, role: "admin" });
    mockUseGridInfoDialogConfiguration.mockReturnValue({ noDataConfiguration: {} });
    mockGetActions.mockReturnValue([{ value: "force_import", label: "Force import" }]);
  });

  describe("useColumns", () => {
    it("returns 9 columns in the expected order", () => {
      const { result } = renderHook(() => useColumns());

      expect(result.current.map((c) => c.name)).toEqual([
        "id",
        "name",
        "type",
        "parent_id",
        "resources_charged_this_month",
        "expenses_so_far_this_month",
        "expenses_forecast_this_month",
        "last_import_at",
        "actions",
      ]);
    });

    it.each([
      ["id", ["id"]],
      ["name", ["name", "datasource_id"]],
      ["type", ["type"]],
      ["parent_id", ["parent_id", "parent.id", "parent.name", "parent.type"]],
      ["resources_charged_this_month", ["resources_charged_this_month"]],
      ["expenses_so_far_this_month", ["expenses_so_far_this_month"]],
      ["expenses_forecast_this_month", ["expenses_forecast_this_month"]],
      ["last_import_at", ["last_import_at"]],
      ["actions", []],
    ])("column '%s' maps to fields %j", (name, expectedFields) => {
      const { result } = renderHook(() => useColumns());
      const column = result.current.find((c) => c.name === name);

      expect(column?.fields).toEqual(expectedFields);
    });

    it("marks the id column as hidden", () => {
      const { result } = renderHook(() => useColumns());
      const idColumn = result.current.find((c) => c.name === "id")!;

      expect(idColumn.isHidden).toBe(true);
    });

    it("hides the actions column when the user is not admin", () => {
      mockUseUserRole.mockReturnValue({ user: null, role: "operations" });
      const { result } = renderHook(() => useColumns());
      const actionsColumn = result.current.find((c) => c.name === "actions")!;

      expect(actionsColumn.isHidden).toBe(true);
    });

    it("shows the actions column when the user is admin", () => {
      mockUseUserRole.mockReturnValue({ user: null, role: "admin" });
      const { result } = renderHook(() => useColumns());
      const actionsColumn = result.current.find((c) => c.name === "actions")!;

      expect(actionsColumn.isHidden).toBe(false);
    });

    it("renders the name column with EntityReferenceCell showing name, datasource_id and type icon", () => {
      const { result } = renderHook(() => useColumns());
      const column = result.current.find((c) => c.name === "name")!;
      const item = {
        id: "internal-1",
        name: "AWS Prod",
        datasource_id: "aws-prod-123",
        type: "aws_cnr",
      } as DatasourceRead;

      const { getByTestId } = render(<>{(column.cell as (item: DatasourceRead) => ReactNode)(item)}</>);

      expect(getByTestId("primary")).toHaveTextContent("AWS Prod");
      expect(getByTestId("secondary")).toHaveTextContent("aws-prod-123");
      expect(getByTestId("custom-icon")).toHaveTextContent("aws_cnr");
    });

    it("renders the parent_id column with parent details when parent is set", () => {
      const { result } = renderHook(() => useColumns());
      const column = result.current.find((c) => c.name === "parent_id")!;
      const item = {
        parent: {
          id: "p-1",
          name: "Parent DS",
          datasource_id: "parent-ds-123",
          type: "azure_tenant",
        },
      } as DatasourceRead;

      const { getByTestId } = render(<>{(column.cell as (item: DatasourceRead) => ReactNode)(item)}</>);

      expect(getByTestId("primary")).toHaveTextContent("Parent DS");
      expect(getByTestId("secondary")).toHaveTextContent("parent-ds-123");
      expect(getByTestId("custom-icon")).toHaveTextContent("azure_tenant");
    });

    it("renders the parent_id column with NO_VALUE when parent is missing", () => {
      const { result } = renderHook(() => useColumns());
      const column = result.current.find((c) => c.name === "parent_id")!;
      const item = { parent: null } as unknown as DatasourceRead;

      const { getByTestId } = render(<>{(column.cell as (item: DatasourceRead) => ReactNode)(item)}</>);

      expect(getByTestId("grid-cell-simple")).toHaveTextContent(NO_VALUE);
    });

    it("renders resources_charged_this_month with empty currency", () => {
      const { result } = renderHook(() => useColumns());
      const column = result.current.find((c) => c.name === "resources_charged_this_month")!;
      const item = { resources_charged_this_month: 12 } as DatasourceRead;

      const { getByTestId } = render(<>{(column.cell as (item: DatasourceRead) => ReactNode)(item)}</>);

      expect(getByTestId("grid-cell-currency")).toHaveTextContent("12|");
    });

    it.each([
      ["expenses_so_far_this_month", "expenses_so_far_this_month", 42],
      ["expenses_forecast_this_month", "expenses_forecast_this_month", 55],
    ])("renders %s with currency from organization context", (columnName, field, value) => {
      const { result } = renderHook(() => useColumns());
      const column = result.current.find((c) => c.name === columnName)!;
      const item = { [field]: value } as unknown as DatasourceRead;

      const { getByTestId } = render(<>{(column.cell as (item: DatasourceRead) => ReactNode)(item)}</>);

      expect(getByTestId("grid-cell-currency")).toHaveTextContent(`${value}|USD`);
    });

    it("falls back to empty currency when organization context is undefined", () => {
      mockUseOrganizationContext.mockReturnValue(undefined);
      const { result } = renderHook(() => useColumns());
      const column = result.current.find((c) => c.name === "expenses_so_far_this_month")!;
      const item = { expenses_so_far_this_month: 7 } as DatasourceRead;

      const { getByTestId } = render(<>{(column.cell as (item: DatasourceRead) => ReactNode)(item)}</>);

      expect(getByTestId("grid-cell-currency")).toHaveTextContent("7|");
    });

    it("renders last_import_at as NO_VALUE when the value is an epoch marker", () => {
      const { result } = renderHook(() => useColumns());
      const column = result.current.find((c) => c.name === "last_import_at")!;
      const item = { last_import_at: 0 } as unknown as DatasourceRead;

      const { getByTestId } = render(<>{(column.cell as (item: DatasourceRead) => ReactNode)(item)}</>);

      expect(getByTestId("grid-cell-simple")).toHaveTextContent(NO_VALUE);
    });

    it("renders last_import_at as a date when the value is real", () => {
      const { result } = renderHook(() => useColumns());
      const column = result.current.find((c) => c.name === "last_import_at")!;
      const item = { last_import_at: "2026-01-15T10:00:00Z" } as unknown as DatasourceRead;

      const { getByTestId } = render(<>{(column.cell as (item: DatasourceRead) => ReactNode)(item)}</>);

      expect(getByTestId("grid-cell-date")).toHaveTextContent("2026-01-15T10:00:00Z");
    });

    it("renders the actions column with dynamic actions for the item", () => {
      const { result } = renderHook(() => useColumns());
      const column = result.current.find((c) => c.name === "actions")!;
      const item = { id: "ds-1" } as DatasourceRead;

      const { getByTestId } = render(<>{(column.cell as (item: DatasourceRead) => ReactNode)(item)}</>);

      expect(getByTestId("actions-item-id")).toHaveTextContent("ds-1");
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
      const typeField = result.current.find((f) => f.name === "type")!;

      expect(typeField).toMatchObject({ type: "list" });
      expect((typeField as { options: Array<{ value: string }> }).options.map((o) => o.value)).toEqual([
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
      const optionsFactory = mockUseReactQueryRqlGrid.mock.calls[0][1];
      const query = { toString: () => "rql-string" };

      const options = optionsFactory(query);
      options.queryFn();

      expect(options.queryKey).toEqual([["OrganizationDataSources"], "rql-string", "org-123"]);
      expect(mockListOrganizationDataSources).toHaveBeenCalledWith("org-123", query);
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

      const arg = mockUseGridAsync.mock.calls[0][0];
      expect(arg).toEqual(
        expect.objectContaining({
          id: "grid__organizations-details-data-sources",
          isDefaultView: true,
          selectedView: "default",
          silentRefresh,
          noDataConfiguration: expect.any(Object),
          onEvent: expect.any(Function),
        }),
      );
      expect(arg.columns).toHaveLength(9);
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
      const onEvent = mockUseGridAsync.mock.calls[0][0].onEvent;
      const item = { id: "ds-1" };

      onEvent({ type: "RowActionTriggered", data: { action: "force_import", item } });

      expect(onAction).toHaveBeenCalledWith("force_import", item, silentRefresh);
    });

    it("ignores non-RowActionTriggered events", () => {
      mockUseGridAsync.mockReturnValue({});
      const onAction = jest.fn();

      renderHook(() => useGridConfig("org-123", onAction));
      const onEvent = mockUseGridAsync.mock.calls[0][0].onEvent;

      onEvent({ type: "SomeOtherEvent", data: {} });

      expect(onAction).not.toHaveBeenCalled();
    });
  });
});
