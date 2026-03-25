import {useMemo, useCallback} from 'react';
// import {useMPTContext, useMPTModal} from '@mpt-extension/sdk-react';
import {http} from '@mpt-extension/sdk';
import {Button} from "@swo/design-system/button";
import {Card} from "@swo/design-system/card";
import {Entity} from '@swo/service';
import {
    Order
} from '@swo/mp-api-model';
import {
    OrganizationRead
} from '@swo/ffc-api-model';

import '../styles.scss';
import {
    Grid,
    GridCellSimple,
    GridDefaultConfiguration,
    GridViewDefinition,
    GridColumnDefinition,
    GridFieldDefinition,
    GridCellTitleSubtitle,
    CallApiParams,
    useGridWithRql
} from "@swo/design-system/grid";
import {RqlQuery} from '@swo/rql-client';
import axios from "axios";

export default () => {
    // const {auth, data} = useMPTContext();

    const views: GridViewDefinition[] = useMemo(() => {
        return [
            {
                name: 'default', title: 'Default', configuration: {
                    sort: [{field: 'audit.created.at', direction: 'desc'}],
                },
            }
        ]
    }, []);

    const columns: GridColumnDefinition<Entity<Order>>[] = useMemo(() => {
        return [
            {
                name: 'ID',
                cell: (item: Entity<Order>) => <GridCellSimple>{item.id}</GridCellSimple>
            },
            {
                name: 'Status',
                cell: (item: Order) => <GridCellSimple>{item.status}</GridCellSimple>
            },
            {
                name: 'price',

                cell: (item: Order) => (
                    <GridCellTitleSubtitle
                        className={'align-right'}
                        title={item.price.PPx1}
                        subtitle={item.price.currency}
                    />
                ),
                initialWidth: 180,
            },
        ]
    }, [])
    const rqlFields: GridFieldDefinition[] = [
        {
            title: 'Id',
            name: 'id',
        }];

    const config = useMemo(
        () =>
            ({
                id: 'grid__rql-example',
                // memoizeId: 'gridWithRqlStory',
                views,
                columns,
                paging: {
                    pageSize: 10,
                    isInfiniteScrollingEnabled: false,
                },
                fields: rqlFields,
                // plugins: plugins,
                selectedView: 'default',
            }) as GridDefaultConfiguration<Entity<Order>>,
        // eslint-disable-next-line react-hooks/exhaustive-deps
        [
            columns
        ]
    );

    async function callApi(query: RqlQuery<Entity<Order>>, {controller}: CallApiParams) {
        const URL = `https://portal.s1.show/public/v1/commerce/orders/?${query}`;
        // const ORG_URL = `https://portal.finops.s1.show/ops/v1/organizations`;
        // const TOKEN = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJGVVNSLTczMDctMjU2OSIsImlhdCI6MTc3MjExNDQzNSwibmJmIjoxNzcyMTE0NDM1LCJhY2NvdW50X2lkIjoiRkFDQy05Njk5LTM3MjkiLCJleHAiOjE3NzIxMTQ3MzV9.ucIShHDtkXIS2n5GorvpTX1XuDl_mqVM4oTolGfXmto';

        console.log('callApi', URL, query);
        const response = await http(URL, {
            signal: controller.signal
            // headers: {Authorization: `Bearer ${TOKEN}`, "Content-Type": "application/json"}
        });

        console.log('API response', response);
        // const response = await fetch(`https://api-rql-poc.azurewebsites.net/ef/products/view?${query}`, { signal: controller.signal });
        if (response.status > 300) {
            throw new Error('Failed to fetch data');
        }

        const {
            data,
            $meta: {pagination},
        } = response.data;

        return {data: data, total: pagination.total};
    }


    const {silentRefresh, ...gridProps} = useGridWithRql<Entity<Order>>(config, callApi);

    return <Card testId={'ffc-operations'}>
        TEST
        <div className=''>
            <Grid<Entity<Order>> {...gridProps}>
                <Grid.Actions>
                    <Button type='primary'>Add</Button>
                </Grid.Actions>
            </Grid>
        </div>
    </Card>
};