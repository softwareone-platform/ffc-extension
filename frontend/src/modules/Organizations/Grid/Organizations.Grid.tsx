import { useMemo, useCallback } from "react";
// import {useMPTContext, useMPTModal} from '@mpt-extension/sdk-react';
import { http } from "@mpt-extension/sdk";
import { Card } from "@swo/design-system/card";
import { OrganizationRead } from "@swo/ffc-api-model";
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

export function OrganizationsGrid() {
  // const {auth, data} = useMPTContext();
  const defaultFilter = { operator: "neq", field: "status", value: "deleted" };
  const sort = [{ field: "event.created.at", direction: "desc" }];
  const tProperties = useFixedT('shared:grid:columns');

  const views: GridViewDefinition[] = useMemo(() => {
    return [
      {
        name: "active",
        title: tProperties("activeOrganizations"),
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
    Omit<GridColumnDefinition<OrganizationRead>, "fields"> & {
      fields: Paths<OrganizationRead>[];
    }
  >;

  const columns: Columns = useMemo(() => {
    return [
      {
        name: "name",
        title: tProperties("organization"),
        fields: ["name", "id", "linked_organization_id"],
        cell: (item: OrganizationRead) => (
          <GridCellTitleSubtitle
            title={item.name}
            subtitle={`${item.id} | ${item.linked_organization_id}`}
          />
        ),
      },
      {
        name: "currency",
        title: "Currency",
        fields: ["currency"],
        cell: (item: OrganizationRead) => (
          <GridCellSimple>{item.currency}</GridCellSimple>
        ),
        initialWidth: 175,
      },
      {
        name: "billing_currency",
        title: "Billing Currency",
        fields: ["billing_currency"],
        cell: (item: OrganizationRead) => (
          <GridCellSimple>
            <DisplayValue value={item.billing_currency} />
          </GridCellSimple>
        ),
        initialWidth: 175,
      },
      {
        name: "operations_additional_id",
        title: "Operations additional ID",
        fields: ["operations_external_id"],
        cell: (item: OrganizationRead) => (
          <GridCellSimple>{item.operations_external_id}</GridCellSimple>
        ),
        initialWidth: 350,
      },
      {
        name: "status",
        title: "Status",
        fields: ["status"],
        // cell: (item: OrganizationRead) => <GridCellSimple>{item.status}</GridCellSimple>,
        cell: (item: OrganizationRead) => (
          <GridCellSimple>
            <StatusChip status={capitalizeFirstLetter(item.status)} />
          </GridCellSimple>
        ),
        initialWidth: 150,
      }
    ];
  }, []);
  const rqlFields: GridFieldDefinition[] = [
    {
      title: "Id",
      name: "id",
    },
    { title: "Name", name: "name" },
    { title: "Currency", name: "currency" },
    { title: "Billing Currency", name: "billing_currency" },
    { title: "Operations additional ID", name: "operations_external_id" },
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
      }) as GridDefaultConfiguration<Entity<OrganizationRead>>,
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [columns, views, defaultFilter, sort],
  );

  async function callApi(
    query: RqlQuery<Entity<OrganizationRead>>,
    { controller }: CallApiParams,
  ) {
    const ORG_URL = `/ops/v1/organizations?${query}`;

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
    Entity<OrganizationRead>
  >(config, callApi);

  return (
    <Card testId={"ffc-operations"}>      
      <Grid<Entity<OrganizationRead>> {...gridProps} />
    </Card>
  );
};
