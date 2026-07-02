/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type LimitOffsetPage_DatasourceRead_ = {
  items: Array<{
    id: string;
    name: string;
    type: 'aws_cnr' | 'azure_cnr' | 'azure_tenant' | 'gcp_cnr' | 'unknown';
    parent?: ({
      id: string;
      name: string;
      type: 'aws_cnr' | 'azure_cnr' | 'azure_tenant' | 'gcp_cnr' | 'unknown';
    } | null);
    parent_id?: (string | null);
    resources_charged_this_month: number;
    expenses_so_far_this_month: number;
    expenses_forecast_this_month: number;
    datasource_id: string;
  }>;
  total: number;
  limit: (number | null);
  offset: number;
};
