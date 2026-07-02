/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type LimitOffsetPage_EmployeeRead_ = {
  items: Array<{
    id: string;
    email: string;
    display_name: string;
    created_at?: string | null;
    last_login?: string | null;
    roles_count?: number | null;
    readonly is_admin: boolean;
  }>;
  total: number;
  limit: number | null;
  offset: number;
};
