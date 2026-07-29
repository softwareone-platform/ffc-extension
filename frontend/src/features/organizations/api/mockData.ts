import { DatasourceRead, EmployeeRead, OrganizationRead } from "@swo/ffc-api-model";

// Static fixtures backing the sandbox organizations API. Shapes match the
// real @swo/ffc-api-model read types so consumers (grids, details) are unaware
// they're running on mock data.

const stamp = {
  at: "2026-01-15T10:00:00Z",
  by: { id: "user-ada", type: "user" as const, name: "Ada Lovelace" },
};
const events = { created: stamp, updated: stamp };

export const mockOrganizations: OrganizationRead[] = [
  {
    id: "org-contoso",
    name: "Contoso Ltd",
    currency: "USD",
    billing_currency: "USD",
    operations_external_id: "OPS-1001",
    status: "active",
    events,
    expenses_info: {
      limit: "100000",
      expenses_last_month: "42000",
      expenses_this_month: "18500",
      expenses_this_month_forecast: "39000",
      possible_monthly_saving: "5200",
    },
  },
  {
    id: "org-fabrikam",
    name: "Fabrikam Inc",
    currency: "EUR",
    billing_currency: "EUR",
    operations_external_id: "OPS-1002",
    status: "active",
    events,
    expenses_info: {
      limit: "50000",
      expenses_last_month: "21000",
      expenses_this_month: "9800",
      expenses_this_month_forecast: "20500",
      possible_monthly_saving: "1800",
    },
  },
  {
    id: "org-northwind",
    name: "Northwind Traders",
    currency: "GBP",
    billing_currency: "GBP",
    operations_external_id: "OPS-1003",
    status: "cancelled",
    events,
    expenses_info: null,
  },
];

export const mockEmployees: EmployeeRead[] = [
  {
    id: "emp-1",
    email: "grace.hopper@contoso.com",
    display_name: "Grace Hopper",
    created_at: "2025-11-02T09:00:00Z",
    last_login: "2026-01-20T14:12:00Z",
    roles_count: 3,
  },
  {
    id: "emp-2",
    email: "alan.turing@contoso.com",
    display_name: "Alan Turing",
    created_at: "2025-12-10T09:00:00Z",
    last_login: "2026-01-19T08:40:00Z",
    roles_count: 1,
  },
];

export const mockDataSources: DatasourceRead[] = [
  {
    id: "ds-1",
    datasource_id: "ds-1",
    name: "AWS Production",
    type: "aws_cnr",
    parent_id: null,
    resources_charged_this_month: 128,
    expenses_so_far_this_month: 8200,
    expenses_forecast_this_month: 17400,
  },
  {
    id: "ds-2",
    datasource_id: "ds-2",
    name: "Azure Tenant",
    type: "azure_tenant",
    parent_id: null,
    resources_charged_this_month: 64,
    expenses_so_far_this_month: 3100,
    expenses_forecast_this_month: 6900,
  },
];
