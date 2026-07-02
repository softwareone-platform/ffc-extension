import { useMemo } from "react";

import { UseAsyncGridConfig, useGridAsync } from "@swo/design-system/grid";
import { OrganizationRead } from "~api/ffc-api-model";
import { Entity } from "@swo/service";

import { useAsyncOptions } from "./useAsyncOptions";
import { useColumns } from "./useColumns";
import { useFields } from "./useFields";
import { useViews } from "./useViews";

export function useGridConfig() {
  const columns = useColumns();
  const fields = useFields();
  const views = useViews();
  const asyncOptions = useAsyncOptions();

  const config = useMemo(
    () =>
      ({
        id: "grid__organizations-list",
        views,
        columns,
        fields,
        isDefaultView: false,
        selectedView: "active",
        ...asyncOptions,
      }) as UseAsyncGridConfig<Entity<OrganizationRead>>,
    [columns, views, fields, asyncOptions],
  );

  const gridProps = useGridAsync(config);
  return { silentRefresh: asyncOptions.silentRefresh, ...gridProps };
}
