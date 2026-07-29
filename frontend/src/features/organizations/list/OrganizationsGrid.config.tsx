import { useMemo } from "react";

import { Link } from "react-router-dom";

import {
  GridCellSimple,
  GridCellTitleSubtitle,
  GridColumnDefinition,
  GridFieldDefinition,
  GridInMemoryConfig,
  useGridInMemory,
} from "@swo/design-system/grid";
import { DisplayValue } from "@swo/design-system/utils";
import { OrganizationRead } from "@swo/ffc-api-model";
import { getStatusLabel } from "@swo/mp-status-chip";
import { Paths } from "@swo/rql-client";

import { mockOrganizations } from "~organizations/api/mockData";
import { Status } from "~shared/components/entity-status-chip/EntityStatusChip";
import { useFixedT } from "~shared/hooks/useFixedT";

// Sandbox: a client-side (in-memory) grid over static data. Columns, fields
// (filter definitions) and views are defined inline here rather than in
// separate useColumns/useFields/useViews hooks — one file per grid.
type Columns = Array<
  Omit<GridColumnDefinition<OrganizationRead>, "fields"> & { fields: Paths<OrganizationRead>[] }
>;

export function useGridConfig() {
  const tColumns = useFixedT("shared:grid:columns");
  const tFields = useFixedT("shared:grid:fields");
  const tView = useFixedT("shared:grid:views");

  const config = useMemo(() => {
    const columns: Columns = [
      {
        name: "name",
        title: tColumns("organization"),
        fields: ["name", "id", "linked_organization_id"],
        cell: (item: OrganizationRead) => (
          <GridCellTitleSubtitle
            title={<Link to={`${item.id}/general`}>{item.name}</Link>}
            subtitle={`${item.id} | ${item.linked_organization_id}`}
          />
        ),
      },
      {
        name: "currency",
        title: tColumns("currency"),
        fields: ["currency"],
        cell: (item: OrganizationRead) => <GridCellSimple>{item.currency}</GridCellSimple>,
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
        cell: (item: OrganizationRead) => (
          <GridCellSimple>
            <Status<OrganizationRead> item={item} />
          </GridCellSimple>
        ),
        initialWidth: 150,
      },
    ];

    const fields: GridFieldDefinition[] = [
      { title: tFields("id"), name: "id" },
      { title: tFields("name"), name: "name" },
      { title: tFields("currency"), name: "currency" },
      { title: tFields("billingCurrency"), name: "billing_currency" },
      { title: tFields("operationsAdditionalId"), name: "operations_external_id" },
      {
        name: "status",
        title: tFields("status"),
        type: "list",
        options: [
          { value: "active", label: getStatusLabel("Active") },
          { value: "cancelled", label: getStatusLabel("New") },
          { value: "deleted", label: getStatusLabel("Deleted") },
        ],
      },
    ];

    const views = [
      {
        name: "active",
        title: tView("activeOrganizations"),
        configuration: {
          filters: {
            operator: "and",
            value: [{ operator: "eq", field: "status", value: "active" }],
          },
          sort: [{ field: "name", direction: "asc" }],
        },
      },
      {
        name: "deleted",
        title: tView("deletedOrganizations"),
        configuration: {
          filters: {
            operator: "and",
            value: [{ operator: "eq", field: "status", value: "deleted" }],
          },
          sort: [{ field: "name", direction: "asc" }],
        },
      },
    ];

    return {
      id: "grid__organizations-list",
      columns,
      fields,
      views,
      isDefaultView: false,
      selectedView: "active",
    } as GridInMemoryConfig<OrganizationRead>;
  }, [tColumns, tFields, tView]);

  return useGridInMemory(mockOrganizations, config);
}
