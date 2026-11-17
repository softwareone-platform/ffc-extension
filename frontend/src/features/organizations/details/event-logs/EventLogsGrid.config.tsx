import { useMemo } from "react";

import { UseAsyncGridConfig, useGridAsync } from "@swo/design-system/grid";

import { OrganizationEventRead } from "~api/ffc-api-model";
import { useGridIdentity } from "~shared/hooks/useGridIdentity";
import { useGridInfoDialogConfiguration } from "~shared/hooks/useGridInfoDialogConfiguration";

import { useAsyncOptions } from "./hooks/useAsyncOptions";
import { useColumns } from "./hooks/useColumns";
import { useFields } from "./hooks/useFields";
import { useViews } from "./hooks/useViews";

export function useGridConfig(organizationId: string) {
  const columns = useColumns();
  const fields = useFields();
  const views = useViews();
  const asyncOptions = useAsyncOptions(organizationId);
  const gridInfoDialogConfig = useGridInfoDialogConfiguration();
  const identity = useGridIdentity("organizations-details-logs");
  const config = useMemo(
    () =>
      ({
        ...identity,
        columns,
        fields,
        views,
        isDefaultView: true,
        selectedView: "default",
        ...asyncOptions,
        ...gridInfoDialogConfig,
      }) as UseAsyncGridConfig<OrganizationEventRead>,
    [identity, columns, fields, views, asyncOptions, gridInfoDialogConfig],
  );

  const gridProps = useGridAsync(config);
  return { silentRefresh: asyncOptions.silentRefresh, refresh: asyncOptions.refresh, ...gridProps };
}
