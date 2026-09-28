import { renderHook, screen } from "@testing-library/react";

import type { GridEvents, GridFieldDefinition } from "@swo/design-system/grid";

import type { AccountType } from "~api/ffc-api-model";
import type { useGridInfoDialogConfiguration } from "~shared/hooks/useGridInfoDialogConfiguration";
import { mapAxiosResponseDataList } from "~shared/utils/mapAxiosResponseDataList";
import { columnByName, makeEmployee, renderColumnCell } from "~test-utils";

import {
  mockGetActions,
  mockListOrganizationEmployees,
  mockUseGridAsync,
  mockUseGridInfoDialogConfiguration,
  mockUseReactQueryRqlGrid,
  mockUseUserRole,
} from "./UsersGrid.config.spec.mocks";

import { useAsyncOptions, useColumns, useFields, useGridConfig } from "./UsersGrid.config";

const COLUMN_FIELDS = [
  ["email", ["email"]],
  ["user", ["display_name", "id"]],
  ["user_type", ["is_admin"]],
  ["roles_count", ["roles_count"]],
  ["last_login", ["last_login"]],
  ["created_at", ["created_at"]],
  ["actions", []],
] as const;

describe("UsersGrid.config", () => {
  beforeEach(() => {
    mockUseUserRole.mockReturnValue({ user: null, role: "admin" });
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

    it.each<[AccountType, boolean]>([
      ["operations", true],
      ["admin", false],
    ])("hides the actions column for role '%s' → isHidden=%s", (role, isHidden) => {
      mockUseUserRole.mockReturnValue({ user: null, role });
      const { result } = renderHook(() => useColumns());

      expect(columnByName(result.current, "actions").isHidden).toBe(isHidden);
    });

    it("renders 'user' column with display_name as title and id as subtitle", () => {
      const { result } = renderHook(() => useColumns());

      renderColumnCell(result.current, "user", makeEmployee({ id: "e-1", display_name: "Jane" }));

      expect(screen.getByTestId("title")).toHaveTextContent("Jane");
      expect(screen.getByTestId("subtitle")).toHaveTextContent("e-1");
    });

    it("falls back to email as the title when display_name is empty", () => {
      const { result } = renderHook(() => useColumns());

      renderColumnCell(
        result.current,
        "user",
        makeEmployee({ id: "e-1", display_name: "", email: "user@example.com" }),
      );

      expect(screen.getByTestId("title")).toHaveTextContent("user@example.com");
    });

    it("renders 'user_type' as an admin chip when is_admin=true", () => {
      const { result } = renderHook(() => useColumns());

      renderColumnCell(result.current, "user_type", makeEmployee({ is_admin: true }));

      const chip = screen.getByTestId("status-chip");
      expect(chip).toHaveTextContent("admin");
      expect(chip).toHaveAttribute("data-color", "success");
    });

    it("renders 'user_type' as a user chip when is_admin=false", () => {
      const { result } = renderHook(() => useColumns());

      renderColumnCell(result.current, "user_type", makeEmployee({ is_admin: false }));

      const chip = screen.getByTestId("status-chip");
      expect(chip).toHaveTextContent("user");
      expect(chip).toHaveAttribute("data-color", "gray");
    });

    it("renders 'last_login' with GridCellDate", () => {
      const { result } = renderHook(() => useColumns());

      renderColumnCell(
        result.current,
        "last_login",
        makeEmployee({ last_login: "2026-01-01T00:00:00Z" }),
      );

      expect(screen.getByTestId("grid-cell-date")).toHaveTextContent("2026-01-01T00:00:00Z");
    });

    it("renders 'actions' with dynamic actions for the item", () => {
      mockGetActions.mockReturnValue([{ value: "make_admin", label: "make_admin" }]);
      const { result } = renderHook(() => useColumns());
      const item = makeEmployee({ id: "e-1" });

      renderColumnCell(result.current, "actions", item);

      expect(screen.getByTestId("actions-item-id")).toHaveTextContent("e-1");
      expect(screen.getByTestId("actions-count")).toHaveTextContent("1");
      expect(mockGetActions).toHaveBeenCalledWith(item);
    });
  });

  describe("useFields", () => {
    it("returns fields in fixed order", () => {
      const { result } = renderHook(() => useFields());

      expect(result.current.map((f) => f.name)).toEqual([
        "id",
        "email",
        "display_name",
        "is_admin",
        "last_login",
        "created_at",
      ]);
    });

    it("exposes is_admin as a list field with true/false options", () => {
      const { result } = renderHook(() => useFields());
      const field = result.current.find((f) => f.name === "is_admin") as GridFieldDefinition;

      expect(field).toMatchObject({ type: "list" });
      expect(field.options!.map((o) => o.value)).toEqual(["true", "false"]);
    });

    it.each(["last_login", "created_at"])("marks '%s' as a date field", (name) => {
      const { result } = renderHook(() => useFields());
      expect(result.current.find((f) => f.name === name)).toMatchObject({ type: "date" });
    });
  });

  describe("useAsyncOptions", () => {
    it("initializes useReactQueryRqlGrid with the OrganizationUsers base query key", () => {
      renderHook(() => useAsyncOptions("org-1"));

      expect(mockUseReactQueryRqlGrid).toHaveBeenCalledWith(
        ["OrganizationUsers", "org-1"],
        expect.any(Function),
      );
    });

    it("builds query options that scope queryKey by organizationId and delegate to listOrganizationEmployees", () => {
      renderHook(() => useAsyncOptions("org-1"));
      const optionsFactory = mockUseReactQueryRqlGrid.mock.lastCall![1];
      const query = { toString: () => "rql-string" };

      const options = optionsFactory(query);
      options.queryFn();

      expect(options.queryKey).toEqual([["OrganizationUsers", "org-1"], "rql-string", "org-1"]);
      expect(mockListOrganizationEmployees).toHaveBeenCalledWith("org-1", query);
    });

    it("wires mapAxiosResponseDataList as the select transform", () => {
      renderHook(() => useAsyncOptions("org-1"));
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

    it("wires columns, fields, and async options into useGridAsync", () => {
      mockUseGridAsync.mockReturnValue({});

      renderHook(() => useGridConfig("org-1"));

      const arg = mockUseGridAsync.mock.lastCall![0];
      expect(arg).toEqual(
        expect.objectContaining({
          id: "ffc-extension__organizations-details-users--admin",
          isDefaultView: true,
          selectedView: "default",
          silentRefresh,
          noDataConfiguration: expect.any(Object),
          onEvent: expect.any(Function),
        }),
      );
      expect(arg.columns).toHaveLength(COLUMN_FIELDS.length);
    });

    it("exposes refresh and silentRefresh alongside the useGridAsync result", () => {
      mockUseGridAsync.mockReturnValue({});

      const { result } = renderHook(() => useGridConfig("org-1"));

      expect(result.current.refresh).toBe(refresh);
      expect(result.current.silentRefresh).toBe(silentRefresh);
    });

    it("forwards RowActionTriggered events to onAction with action, item, and silentRefresh", () => {
      mockUseGridAsync.mockReturnValue({});
      const onAction = jest.fn();

      renderHook(() => useGridConfig("org-1", onAction));
      const onEvent = mockUseGridAsync.mock.lastCall![0].onEvent!;

      onEvent({ type: "RowActionTriggered", data: { action: "make_admin", item: { id: "e-1" } } });

      expect(onAction).toHaveBeenCalledWith("make_admin", { id: "e-1" }, silentRefresh);
    });

    it("ignores events that are not RowActionTriggered", () => {
      mockUseGridAsync.mockReturnValue({});
      const onAction = jest.fn();

      renderHook(() => useGridConfig("org-1", onAction));
      const onEvent = mockUseGridAsync.mock.lastCall![0].onEvent!;

      onEvent({ type: "SomethingElse", data: {} } as unknown as GridEvents);

      expect(onAction).not.toHaveBeenCalled();
    });

    it("safely no-ops on RowActionTriggered when no onAction is provided", () => {
      mockUseGridAsync.mockReturnValue({});

      renderHook(() => useGridConfig("org-1"));
      const onEvent = mockUseGridAsync.mock.lastCall![0].onEvent!;

      expect(() =>
        onEvent({
          type: "RowActionTriggered",
          data: { action: "make_admin", item: { id: "e-1" } },
        }),
      ).not.toThrow();
    });
  });
});
