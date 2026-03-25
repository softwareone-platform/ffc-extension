export type GetDatasourcesByOrganizationIDResponse = [
  {
    id: string; // UUID
    name: string;
    type: 'aws_cnr' | 'azure_cnr' | 'azure_tenant' | 'gcp_cnr' | 'unknown';
    parent_id?: string | null; // UUID or null
    resources_charged_this_month: number;
    expenses_so_far_this_month: number;
    expenses_forecast_this_month: number;
  },
];
