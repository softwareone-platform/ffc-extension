import { useCallback, useMemo } from "react";

import { GridEvents, UseAsyncGridConfig, useGridAsync } from "@swo/design-system/grid";
import { Entity } from "@swo/service";

import { OrganizationRead } from "~api/ffc-api-model";
import { useDefaultView } from "~shared/hooks/useDefaultView";

import { Organization, OrganizationAction } from "../api/model";
import { useAsyncOptions } from "./hooks/useAsyncOptions";
import { useColumns } from "./hooks/useColumns";
import { useFields } from "./hooks/useFields";
import { useViews } from "./hooks/useViews";

export function useGridConfig(
  onAction?: (action: OrganizationAction, item: Organization, silentRefresh: () => void) => void,
) {
  const columns = useColumns();
  const fields = useFields();
  const views = useViews();
  const asyncOptions = useAsyncOptions();
  const defaultView = useDefaultView();

  const onGridActionEvent = useCallback(
    (event: GridEvents) => {
      if (event.type === "RowActionTriggered") {
        onAction?.(
          event.data.action as OrganizationAction,
          event.data.item as Organization,
          asyncOptions.silentRefresh,
        );
      }
    },
    [asyncOptions.silentRefresh, onAction],
  );

  const config = useMemo(
    () =>
      ({
        id: "grid__organizations-list",
        views,
        columns,
        fields,
        ...defaultView,
        ...asyncOptions,
        onEvent: onGridActionEvent,
      }) as UseAsyncGridConfig<Entity<OrganizationRead>>,
    [columns, views, fields, asyncOptions, onGridActionEvent],
  );

  const gridProps = useGridAsync(config);
  return { refresh: asyncOptions.refresh, silentRefresh: asyncOptions.silentRefresh, ...gridProps };
}
