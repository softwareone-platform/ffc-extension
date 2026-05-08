import { useMemo } from 'react';

import { GridFieldDefinition } from '@swo/design-system/grid';
import {
    GridCellSimple,
    GridColumnDefinition,
    UseAsyncGridConfig,
    useGridAsync,
} from '@swo/design-system/grid';
import { DatasourceRead } from '@swo/ffc-api-model';
import { Paths } from '@swo/rql-client';

import { useOrganizationsApi } from '~organizations/api';
import { useFixedT } from '~shared/hooks/use-fixed-t';
import { useReactQueryRqlGrid } from '~shared/hooks/use-react-query-rql-grid';

const defaultFilter = {
    operator: 'and',
    value: [{ operator: 'eq', field: 'status', value: 'active' }],
};
const sort = [{ field: 'event.created.at', direction: 'desc' }];

type Columns = Array<
    Omit<GridColumnDefinition<DatasourceRead>, 'fields'> & {
        fields: Paths<DatasourceRead>[];
    }
>;

export function useColumns(): Columns {
    const tColumns = useFixedT('shared:grid:columns');

    return useMemo(() => {
        return [
            {
                name: 'id',
                title: tColumns('id'),
                fields: ['id'],
                cell: (item: DatasourceRead) => <GridCellSimple>{item.id}</GridCellSimple>,
            },
            {
                name: 'name',
                title: tColumns('name'),
                fields: ['name'],
                cell: (item: DatasourceRead) => <GridCellSimple>{item.name}</GridCellSimple>,
            },
            {
                name: 'type',
                title: tColumns('type'),
                fields: ['type'],
                cell: (item: DatasourceRead) => <GridCellSimple>{item.type}</GridCellSimple>,
            },
            {
                name: 'actions',
                title: tColumns('actions'),
                fields: [],
                cell: (item: DatasourceRead) => <></>,
                initialWidth: 100,
            },
        ];
    }, []);
}

export function useFields() {
    const tColumns = useFixedT('shared:grid:columns');
    const tFields = useFixedT('shared:grid:fields');

    return useMemo(
        (): GridFieldDefinition[] => [
            {
                title: tFields('id'),
                name: 'id',
            },
            { title: tFields('name'), name: 'name' },
            { title: tFields('type'), name: 'type' },
        ],
        [tFields],
    );
}

export function useAsyncOptions(organizationId: string) {
    const { listOrganizationDataSources } = useOrganizationsApi();
    const baseQueryKey = ['OrganizationDataSources', organizationId] as const;
    return useReactQueryRqlGrid<
        DatasourceRead,
        Awaited<ReturnType<typeof listOrganizationDataSources>>
    >(baseQueryKey, (query) => ({
        queryKey: [...baseQueryKey, query.toString()] as const,
        queryFn: () => listOrganizationDataSources(organizationId, query),
        select: (res) => {
            return { data: res.data, total: undefined };
        },
    }));
}

export function useGridConfig(organizationId: string) {
    const columns = useColumns();
    const fields = useFields();
    // const views = useViews();
    const asyncOptions = useAsyncOptions(organizationId);

    const config = useMemo(
        () =>
            ({
                id: 'grid__organizations-details-data-sources',
                // memoizeId: 'gridWithRqlStory',
                // views,
                columns,
                fields,
                isDefaultView: true,
                selectedView: 'default',
                ...asyncOptions,
            }) as UseAsyncGridConfig<DatasourceRead>,
        [columns, defaultFilter, sort, fields, asyncOptions],
    );

    const gridProps = useGridAsync(config);
    return { silentRefresh: asyncOptions.silentRefresh, ...gridProps };
}
