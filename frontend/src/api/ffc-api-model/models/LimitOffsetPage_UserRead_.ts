/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type LimitOffsetPage_UserRead_ = {
  items: Array<{
    name: string;
    external_id: string;
    email: string;
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
    status: "draft" | "active" | "disabled" | "deleted";
    account_user: {
      status: "invited" | "invitation-expired" | "active" | "deleted";
      id: string;
      created_at?: string | null;
      joined_at?: string | null;
      account: {
        id: string;
        name: string;
        type: "admin" | "operations" | "affiliate";
        integration: "aws" | "google" | "microsoft" | "softwareone" | null;
        /**
         * An external identifier for the account
         */
        external_id: string;
      };
    } | null;
  }>;
  total: number;
  limit: number | null;
  offset: number;
};
