import { Entity } from '@swo/service';
import { OrganizationRead } from '@swo/ffc-api-model';
import { UseAsyncGridConfig, useGridAsync } from '@swo/design-system/grid';
import { useAsyncOptions } from '../hooks/useAsyncOptions';
import { useColumns } from '../hooks/useColumns';
import { useFields } from '../hooks/useFields';
import { useMemo } from 'react';
import { useViews } from '../hooks/useViews';

const defaultFilter = {
  operator: "and",
  value: [{ operator: "eq", field: "status", value: "active" }],
};
const sort = [{ field: "event.created.at", direction: "desc" }];

export function useGridConfig() {
  const columns = useColumns();
  const fields = useFields();
  const views = useViews();
  const asyncOptions = useAsyncOptions();

  const config = useMemo(
    () =>
      ({
        id: "grid__rql-example",
        // memoizeId: 'gridWithRqlStory',
        views,
        columns,
        fields,
        isDefaultView: false,
        selectedView: "active",
        ...asyncOptions,
      }) as UseAsyncGridConfig<Entity<OrganizationRead>>,
    [columns, views, defaultFilter, sort, fields, asyncOptions],
  );

  //   const { list } = useOrganizationsApi();

  //   const { silentRefresh, ...gridProps } = useGridWithRql<
  //     Entity<OrganizationRead>
  //   >(config, list);

  const gridProps = useGridAsync(config);
  return { silentRefresh: asyncOptions.silentRefresh, ...gridProps };
  //   const gridProps = useGridAsync(options);
  //   return { silentRefresh, ...gridProps };
}
