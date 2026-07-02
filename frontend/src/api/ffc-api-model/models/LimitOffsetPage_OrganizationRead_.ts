/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type LimitOffsetPage_OrganizationRead_ = {
  items: Array<{
    name: string;
    currency: string;
    billing_currency: string;
    operations_external_id: string;
    events: {
      created: {
        at: string;
        by: {
          id: string;
          type: "user" | "system";
          name: string;
        } | null;
      };
      updated: {
        at: string;
        by: {
          id: string;
          type: "user" | "system";
          name: string;
        } | null;
      };
      deleted?: {
        at: string;
        by: {
          id: string;
          type: "user" | "system";
          name: string;
        } | null;
      } | null;
    };
    id: string;
    linked_organization_id?: string | null;
    status: "active" | "cancelled" | "deleted";
    expenses_info?: {
      limit?: string;
      expenses_this_month?: string;
      expenses_this_month_forecast?: string;
      possible_monthly_saving?: string;
    } | null;
  }>;
  total: number;
  limit: number | null;
  offset: number;
};
