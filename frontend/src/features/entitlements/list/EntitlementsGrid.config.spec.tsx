import { renderHook, screen } from "@testing-library/react";

import type { GridEvents, GridFieldDefinition } from "@swo/design-system/grid";

import type { useGridInfoDialogConfiguration } from "~shared/hooks/useGridInfoDialogConfiguration";
import { mapAxiosResponseDataList } from "~shared/utils/mapAxiosResponseDataList";
import { columnByName, makeEntitlement, renderColumnCell } from "~test-utils";

import {
  mockGetActions,
  mockListEntitlements,
  mockStatus,
  mockUseGridAsync,
  mockUseGridInfoDialogConfiguration,
  mockUseReactQueryRqlGrid,
} from "./EntitlementsGrid.config.spec.mocks";

import type { Entitlement } from "../api/model";
import {
  useAsyncOptions,
  useColumns,
  useFields,
  useGridConfig,
  useViews,
} from "./EntitlementsGrid.config";

const COLUMN_FIELDS = [
  ["name", ["id", "name"]],
  ["affiliate", ["owner.id", "owner.name", "owner.external_id", "owner.integration"]],
  ["data_source", ["linked_datasource_name", "linked_datasource_type", "datasource_id"]],
  ["organization", ["events.redeemed.by.id", "events.redeemed.by.name"]],
  ["linked_datasource_id", ["linked_datasource_id"]],
  ["affiliate_external_id", ["affiliate_external_id"]],
  ["updated_at", ["events.updated.at"]],
  ["created_at", ["events.created.at"]],
  ["redeemed_at", ["events.redeemed.at"]],
  ["terminated_at", ["events.terminated.at"]],
  ["deleted_at", ["events.deleted.at"]],
  ["status", ["status"]],
  ["actions", []],
] as const;

describe("EntitlementsGrid.config", () => {
  beforeEach(() => {
    mockUseGridInfoDialogConfiguration.mockReturnValue({
      noDataConfiguration: {},
    } as ReturnType<typeof useGridInfoDialogConfiguration>);
  });

  describe("useColumns", () => {
    it("returns columns in fixed order", () => {
      const { result } = renderHook(() => useColumns());

      expect(result.current.map((c) => c.name)).toEqual(COLUMN_FIELDS.map(([n]) => n));
    });

    it.each(COLUMN_FIELDS)("column '%s' maps to fields %j", (name, expectedFields) => {
      const { result } = renderHook(() => useColumns());

      expect(columnByName(result.current, name).fields).toEqual(expectedFields);
    });

    it("renders 'name' column with a link title and id subtitle", () => {
      const { result } = renderHook(() => useColumns());

      renderColumnCell(result.current, "name", makeEntitlement({ id: "ent-1", name: "One" }));

      expect(screen.getByTestId("title")).toHaveTextContent("One");
      expect(screen.getByTestId("subtitle")).toHaveTextContent("ent-1");
    });

    it("renders 'affiliate' column via EntityReference with owner details", () => {
      const { result } = renderHook(() => useColumns());

      renderColumnCell(
        result.current,
        "affiliate",
        makeEntitlement({
          owner: {
            id: "own-1",
            external_id: "ext",
            name: "Owner Name",
            type: "affiliate",
            integration: "google",
          },
        }),
      );

      expect(screen.getByTestId("entity-primary")).toHaveTextContent("Owner Name");
      expect(screen.getByTestId("entity-secondary")).toHaveTextContent("own-1");
      expect(screen.getByTestId("custom-icon")).toHaveTextContent("google");
    });

    it("renders 'data_source' column via DataSourceEntityReference with the item", () => {
      const { result } = renderHook(() => useColumns());
      const item = makeEntitlement({ id: "ent-42" });

      renderColumnCell(result.current, "data_source", item);

      expect(screen.getByTestId("datasource-entity-reference")).toHaveAttribute(
        "data-entity-id",
        "ent-42",
      );
    });

    it("renders NO_VALUE for the 'organization' column when the entitlement has not been redeemed", () => {
      const { result } = renderHook(() => useColumns());

      renderColumnCell(
        result.current,
        "organization",
        makeEntitlement({
          events: { redeemed: null } as unknown as Entitlement["events"],
        }),
      );

      expect(screen.getByTestId("grid-cell-simple")).toHaveTextContent("—");
    });

    it("renders 'organization' column with title/subtitle when redeemed", () => {
      const { result } = renderHook(() => useColumns());

      renderColumnCell(
        result.current,
        "organization",
        makeEntitlement({
          events: {
            redeemed: { by: { id: "org-1", name: "Org One" } },
          } as unknown as Entitlement["events"],
        }),
      );

      expect(screen.getByTestId("title")).toHaveTextContent("Org One");
      expect(screen.getByTestId("subtitle")).toHaveTextContent("org-1");
    });

    it.each([
      ["updated_at", "updated"],
      ["created_at", "created"],
      ["redeemed_at", "redeemed"],
      ["terminated_at", "terminated"],
      ["deleted_at", "deleted"],
    ] as const)(
      "renders '%s' column with GridCellDateTime from events.%s.at",
      (columnName, key) => {
        const { result } = renderHook(() => useColumns());
        const events = { [key]: { at: "2026-01-15T10:00:00Z" } };

        renderColumnCell(
          result.current,
          columnName,
          makeEntitlement({ events: events as unknown as Entitlement["events"] }),
        );

        expect(screen.getByTestId("grid-cell-date-time")).toHaveTextContent("2026-01-15T10:00:00Z");
      },
    );

    it("renders 'status' column with the Status chip", () => {
      const { result } = renderHook(() => useColumns());
      const item = makeEntitlement({ status: "active" });

      renderColumnCell(result.current, "status", item);

      expect(mockStatus).toHaveBeenCalledWith({ item });
    });

    it("renders 'actions' column with dynamic actions for the item", () => {
      mockGetActions.mockReturnValue([{ value: "terminate", label: "terminate" }]);
      const { result } = renderHook(() => useColumns());
      const item = makeEntitlement({ id: "ent-1" });

      renderColumnCell(result.current, "actions", item);

      expect(screen.getByTestId("actions-item-id")).toHaveTextContent("ent-1");
      expect(screen.getByTestId("actions-count")).toHaveTextContent("1");
      expect(mockGetActions).toHaveBeenCalledWith(item);
    });
  });

  describe("useFields", () => {
    it("exposes linked_datasource_type as a list field with azure_cnr and aws_cnr options", () => {
      const { result } = renderHook(() => useFields());
      const field = result.current.find(
        (f) => f.name === "linked_datasource_type",
      ) as GridFieldDefinition;

      expect(field).toMatchObject({ type: "list" });
      expect(field.options!.map((o) => o.value)).toEqual(["azure_cnr", "aws_cnr"]);
    });

    it("exposes status as a list field with all four options", () => {
      const { result } = renderHook(() => useFields());
      const field = result.current.find((f) => f.name === "status") as GridFieldDefinition;

      expect(field).toMatchObject({ type: "list" });
      expect(field.options!.map((o) => o.value)).toEqual([
        "active",
        "new",
        "terminated",
        "deleted",
      ]);
    });

    it.each([
      "events.created.at",
      "events.updated.at",
      "events.redeemed.at",
      "events.terminated.at",
      "events.deleted.at",
    ])("marks '%s' as a date field", (name) => {
      const { result } = renderHook(() => useFields());

      expect(result.current.find((f) => f.name === name)).toMatchObject({ type: "date" });
    });
  });

  describe("useViews", () => {
    it("returns main, active, inactive, and all views in fixed order", () => {
      const { result } = renderHook(() => useViews());

      expect(result.current.map((v) => v.name)).toEqual(["main", "active", "inactive", "all"]);
    });

    it("scopes the main view to non-deleted entitlements sorted by updated desc", () => {
      const { result } = renderHook(() => useViews());
      const main = result.current.find((v) => v.name === "main")!;

      expect(main.configuration).toMatchObject({
        filters: {
          operator: "or",
          value: [{ operator: "neq", field: "status", value: "deleted" }],
        },
        sort: [{ field: "events.updated.at", direction: "desc" }],
      });
    });

    it("scopes the inactive view to deleted or terminated statuses", () => {
      const { result } = renderHook(() => useViews());
      const inactive = result.current.find((v) => v.name === "inactive")!;

      expect(inactive.configuration.filters).toEqual({
        operator: "or",
        value: [
          { operator: "eq", field: "status", value: "deleted" },
          { operator: "eq", field: "status", value: "terminated" },
        ],
      });
    });
  });

  describe("useAsyncOptions", () => {
    it("initializes useReactQueryRqlGrid with the EntitlementsList base query key", () => {
      renderHook(() => useAsyncOptions());

      expect(mockUseReactQueryRqlGrid).toHaveBeenCalledWith(
        ["EntitlementsList"],
        expect.any(Function),
      );
    });

    it("builds query options that add the query string to the queryKey and delegate to list()", () => {
      renderHook(() => useAsyncOptions());
      const optionsFactory = mockUseReactQueryRqlGrid.mock.lastCall![1];
      const query = { toString: () => "rql-string" };

      const options = optionsFactory(query);
      options.queryFn();

      expect(options.queryKey).toEqual([["EntitlementsList"], "rql-string"]);
      expect(mockListEntitlements).toHaveBeenCalledWith(query);
    });

    it("wires mapAxiosResponseDataList as the select transform", () => {
      renderHook(() => useAsyncOptions());
      const optionsFactory = mockUseReactQueryRqlGrid.mock.lastCall![1];

      const options = optionsFactory({ toString: () => "rql" });

      expect(options.select).toBe(mapAxiosResponseDataList);
    });
  });

  describe("useGridConfig", () => {
    const silentRefresh = jest.fn();
    const refresh = jest.fn();

    beforeEach(() => {
      mockUseReactQueryRqlGrid.mockReturnValue({ silentRefresh, refresh });
    });

    it("wires columns, fields, views, async options, and info-dialog config into useGridAsync", () => {
      mockUseGridAsync.mockReturnValue({});

      renderHook(() => useGridConfig());

      const arg = mockUseGridAsync.mock.lastCall![0];
      expect(arg).toEqual(
        expect.objectContaining({
          id: "entitlements-list",
          memoizeId: "entitlements-list",
          isDefaultView: false,
          selectedView: "main",
          silentRefresh,
          noDataConfiguration: expect.any(Object),
          onEvent: expect.any(Function),
        }),
      );
      expect(arg.columns).toHaveLength(COLUMN_FIELDS.length);
    });

    it("exposes refresh and silentRefresh alongside the useGridAsync result", () => {
      mockUseGridAsync.mockReturnValue({ extra: 1 });

      const { result } = renderHook(() => useGridConfig());

      expect(result.current.refresh).toBe(refresh);
      expect(result.current.silentRefresh).toBe(silentRefresh);
    });

    it("forwards RowActionTriggered events to onAction with action, item, and silentRefresh", () => {
      mockUseGridAsync.mockReturnValue({});
      const onAction = jest.fn();

      renderHook(() => useGridConfig(onAction));
      const onEvent = mockUseGridAsync.mock.lastCall![0].onEvent!;

      onEvent({ type: "RowActionTriggered", data: { action: "terminate", item: { id: "e-1" } } });

      expect(onAction).toHaveBeenCalledWith("terminate", { id: "e-1" }, silentRefresh);
    });

    it("ignores events that are not RowActionTriggered", () => {
      mockUseGridAsync.mockReturnValue({});
      const onAction = jest.fn();

      renderHook(() => useGridConfig(onAction));
      const onEvent = mockUseGridAsync.mock.lastCall![0].onEvent!;

      onEvent({ type: "SomethingElse", data: {} } as unknown as GridEvents);

      expect(onAction).not.toHaveBeenCalled();
    });
  });
});
