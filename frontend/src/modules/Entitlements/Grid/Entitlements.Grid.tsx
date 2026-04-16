import { useMemo, useCallback } from "react";
// import {useMPTContext, useMPTModal} from '@mpt-extension/sdk-react';
import { http } from "@mpt-extension/sdk";
import { Card } from "@swo/design-system/card";
import { EntitlementRead } from "@swo/ffc-api-model";
import { StatusChip } from "@swo/mp-status-chip";

import "../../../styles.scss";
import {
  Grid,
  GridCellSimple,
  GridDefaultConfiguration,
  GridViewDefinition,
  GridColumnDefinition,
  GridFieldDefinition,
  GridCellTitleSubtitle,
  CallApiParams,
  useGridWithRql,
} from "@swo/design-system/grid";
import { Paths, RqlQuery } from "@swo/rql-client";
import { Entity } from "@swo/service";
import { DisplayValue } from "@swo/design-system/utils";
import { useFixedT } from "../../../hooks/useFixedT";

function capitalizeFirstLetter(val) {
    return String(val).charAt(0).toUpperCase() + String(val).slice(1);
}

export default () => {
  // const {auth, data} = useMPTContext();
  const defaultFilter = { operator: "neq", field: "status", value: "deleted" };
  const sort = [{ field: "event.created.at", direction: "desc" }];
  const tProperties = useFixedT('shared:grid:columns');

  const views: GridViewDefinition[] = useMemo(() => {
    return [
      {
        name: "active",
        title: tProperties("activeEntitlements"),
        configuration: {
          filters: {
            operator: "and",
            value: [{ operator: "eq", field: "status", value: "active" }],
          },
          sort: [{ field: "name", direction: "asc" }],
        },
      },
    ];
  }, []);

  type Columns = Array<
    Omit<GridColumnDefinition<EntitlementRead>, "fields"> & {
      fields: Paths<EntitlementRead>[];
    }
  >;

  const columns: Columns = useMemo(() => {
    return [
      {
        name: "name",
        title: tProperties("entitlement"),
        fields: ["name", "id"],
        cell: (item: EntitlementRead) => (
          <GridCellTitleSubtitle
            title={item.name}
            subtitle={`${item.id}`}
          />
        ),
      },
      {
        name: "affiliate_external_id",
        title: "Affiliate External ID",
        fields: ["affiliate_external_id"],
        cell: (item: EntitlementRead) => (
          <GridCellSimple>{item.affiliate_external_id}</GridCellSimple>
        ),
        initialWidth: 300,
      },
      
      {
        name: "data_source",
        title: "Data Source",
        fields: ["linked_datasource_name", "linked_datasource_id", "linked_datasource_type"],
        cell: (item: EntitlementRead) => (          
          <GridCellTitleSubtitle
            title={item.linked_datasource_name}
            subtitle={`${item.linked_datasource_id} | ${item.linked_datasource_type}`}
          />
        ),
        initialWidth: 350,
      },
      {
        name: "status",
        title: "Status",
        fields: ["status"],
        // cell: (item: EntitlementRead) => <GridCellSimple>{item.status}</GridCellSimple>,
        cell: (item: EntitlementRead) => (
          <GridCellSimple>
            <StatusChip status={capitalizeFirstLetter(item.status)} />
          </GridCellSimple>
        ),
        initialWidth: 150,
      },
      // {
      //     name: 'price',
      //
      //     cell: (item: Order) => (
      //         <GridCellTitleSubtitle
      //             className={'align-right'}
      //             title={item.price.PPx1}
      //             subtitle={item.price.currency}
      //         />
      //     ),
      //     initialWidth: 180,
      // },
    ];
  }, []);
  const rqlFields: GridFieldDefinition[] = [
    {
      title: "Id",
      name: "id",
    },
    { title: "Name", name: "name" },
    { title: "Affiliate External ID", name: "affiliate_external_id" },
    { title: "Data Source", name: "linked_datasource_name" },
    { title: "Data Source ID", name: "linked_datasource_id" },
    { title: "Data Source Type", name: "linked_datasource_type" },
    { title: "Status", name: "status" },
  ];

  const config = useMemo(
    () =>
      ({
        id: "grid__rql-example",
        // memoizeId: 'gridWithRqlStory',
        views,
        columns,
        filter: defaultFilter,
        sort,
        paging: {
          pageSize: 10,
          isInfiniteScrollingEnabled: false,
        },
        fields: rqlFields,
        // plugins: plugins,
        selectedView: "default",
      }) as GridDefaultConfiguration<Entity<EntitlementRead>>,
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [columns, views, defaultFilter, sort],
  );

  async function callApi(
    query: RqlQuery<Entity<EntitlementRead>>,
    { controller }: CallApiParams,
  ) {
    const ORG_URL = `/ops/v1/entitlements?${query}`;

    const response = await http(ORG_URL, {
      signal: controller.signal,
    });

    if (response.status > 300) {
      throw new Error("Failed to fetch data");
    }

    const { items, total } = response.data;

    return { data: items, total };
  }

  const { silentRefresh, ...gridProps } = useGridWithRql<
    Entity<EntitlementRead>
  >(config, callApi);

  return (
    <Card testId={"ffc-operations"}>      
      <Grid<Entity<EntitlementRead>> {...gridProps} />
    </Card>
  );
};
