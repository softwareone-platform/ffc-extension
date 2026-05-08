import { EmployeeRead } from '@swo/ffc-api-model';
import { GridFieldDefinition } from '@swo/design-system/grid';
import { Paths } from '@swo/rql-client';
import { useFixedT } from '~shared/hooks/use-fixed-t';
import { useMemo } from 'react';
import { useOrganizationsApi } from '../../api/use-organizations-api';
import { useReactQueryRqlGrid } from '~shared/hooks/use-react-query-rql-grid';
import {
    GridCellSimple,
    GridCellTitleSubtitle,
    GridColumnDefinition,
    UseAsyncGridConfig,
    useGridAsync,
} from '@swo/design-system/grid';
// import { useAsyncOptions } from "../hooks/useAsyncOptions";

// import { useViews } from "../hooks/useViews";

const defaultFilter = {
    operator: 'and',
    value: [{ operator: 'eq', field: 'status', value: 'active' }],
};
const sort = [{ field: 'event.created.at', direction: 'desc' }];

type Columns = Array<
    Omit<GridColumnDefinition<EmployeeRead>, 'fields'> & {
        fields: Paths<EmployeeRead>[];
    }
>;

export function useColumns(): Columns {
    const tColumns = useFixedT('shared:grid:columns');

    return useMemo(() => {
        return [
            {
                name: 'email',
                title: tColumns('organization'),
                fields: ['email'],
                cell: (item: EmployeeRead) => <GridCellSimple>{item.email}</GridCellSimple>,
            },
            {
                name: 'user',
                title: tColumns('user'),
                fields: ['display_name', 'id'],
                cell: (item: EmployeeRead) => (
                    <GridCellTitleSubtitle
                        title={item.display_name || item.email}
                        subtitle={item.id}
                    />
                ),
            },
            {
                name: 'roles_count',
                title: tColumns('rolesCount'),
                fields: ['roles_count'],
                cell: (item: EmployeeRead) => <GridCellSimple>{item.roles_count}</GridCellSimple>,
                initialWidth: 150,
            },
            {
                name: 'actions',
                title: tColumns('actions'),
                fields: [],
                cell: (item: EmployeeRead) => <></>,
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
            { title: tFields('email'), name: 'email' },
            { title: tFields('displayName'), name: 'display_name' },
            { title: tFields('rolesCount'), name: 'roles_count' },
        ],
        [tFields],
    );
}

export function useAsyncOptions(organizationId: string) {
    const { listOrganizationEmployees } = useOrganizationsApi();
    const baseQueryKey = ['OrganizationUsers', organizationId] as const;
    return useReactQueryRqlGrid<
        EmployeeRead,
        Awaited<ReturnType<typeof listOrganizationEmployees>>
    >(baseQueryKey, (query) => ({
        queryKey: [...baseQueryKey, query.toString()] as const,
        queryFn: () => listOrganizationEmployees(organizationId, query),
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
                id: 'grid__organizations-details-users',
                // memoizeId: 'gridWithRqlStory',
                // views,
                columns,
                fields,
                isDefaultView: true,
                selectedView: 'default',
                ...asyncOptions,
            }) as UseAsyncGridConfig<EmployeeRead>,
        [columns, defaultFilter, sort, fields, asyncOptions],
    );

    const gridProps = useGridAsync(config);
    return { silentRefresh: asyncOptions.silentRefresh, ...gridProps };
}
