/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type DatasourceExpenseRead = {
  events: {
    created: {
      at: string;
      by: ({
        id: string;
        type: 'user' | 'system';
        name: string;
      } | null);
    };
    updated: {
      at: string;
      by: ({
        id: string;
        type: 'user' | 'system';
        name: string;
      } | null);
    };
    deleted?: ({
      at: string;
      by: ({
        id: string;
        type: 'user' | 'system';
        name: string;
      } | null);
    } | null);
  };
  id: string;
  datasource_id: string;
  linked_datasource_id: string;
  datasource_name: string;
  linked_datasource_type: 'aws_cnr' | 'azure_cnr' | 'azure_tenant' | 'gcp_cnr' | 'unknown';
  organization: {
    id: string;
    name: string;
    operations_external_id: string;
  };
  year: number;
  day: number;
  month: number;
  expenses: string;
  total_expenses: string;
};
