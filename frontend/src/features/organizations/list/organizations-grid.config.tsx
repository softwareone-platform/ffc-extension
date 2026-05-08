import { useMemo } from 'react';

import { UseAsyncGridConfig, useGridAsync } from '@swo/design-system/grid';
import { OrganizationRead } from '@swo/ffc-api-model';
import { Entity } from '@swo/service';

import { useAsyncOptions } from './use-async-options';
import { useColumns } from './use-columns';
import { useFields } from './use-fields';
import { useViews } from './use-views';

const _defaultFilter = {
    operator: 'and',
    value: [{ operator: 'eq', field: 'status', value: 'active' }],
};
const _sort = [{ field: 'event.created.at', direction: 'desc' }];

export function useGridConfig() {
    const columns = useColumns();
    const fields = useFields();
    const views = useViews();
    const asyncOptions = useAsyncOptions();

    const config = useMemo(
        () =>
            ({
                id: 'grid__rql-example',
                // memoizeId: 'gridWithRqlStory',
                views,
                columns,
                fields,
                isDefaultView: false,
                selectedView: 'active',
                ...asyncOptions,
            }) as UseAsyncGridConfig<Entity<OrganizationRead>>,
        [columns, views, fields, asyncOptions],
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
