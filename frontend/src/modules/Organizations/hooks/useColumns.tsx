import { DisplayValue } from '@swo/design-system/utils';
import { GridCellSimple, GridCellTitleSubtitle, GridColumnDefinition } from '@swo/design-system/grid';
import { GridStatusCell } from '../../../shared/components/GridStatusCell';
import { OrganizationRead } from '@swo/ffc-api-model';
import { Paths } from '@swo/rql-client';
import { useFixedT } from '../../../shared/hooks/useFixedT';
import { useMemo } from 'react';

import { Link } from "react-router";



type Columns = Array<
  Omit<GridColumnDefinition<OrganizationRead>, "fields"> & {
    fields: Paths<OrganizationRead>[];
  }
>;

export function useColumns(): Columns {
const tColumns = useFixedT("shared:grid:columns");

  return useMemo(() => {
    return [
      {
        name: "name",
        title: tColumns("organization"),
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
          <GridStatusCell<OrganizationRead> item={item} />
        ),
        initialWidth: 150,
      },
      {
        name: "link",
        title: tColumns("link"),
        fields: ["name", "id", "linked_organization_id"],
        cell: (item: OrganizationRead) => (
          <GridCellSimple>            
            <Link to={`/${item.id}/details`}>View details</Link>
          </GridCellSimple>
        ),
      },
    ];
  }, []);
}
