/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type AccountRead = {
  /**
   * The name of the account
   */
  name: string;
  /**
   * An external identifier for the account
   */
  external_id: string;
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
  account_user: {
    status: "invited" | "invitation-expired" | "active" | "deleted";
    id: string;
    created_at?: string | null;
    joined_at?: string | null;
    user: {
      name: string;
      external_id: string;
      email: string;
      id: string;
    };
  } | null;
  integration?: "aws" | "google" | "microsoft" | "softwareone" | null;
  status: "active" | "disabled" | "deleted";
  type: "admin" | "operations" | "affiliate";
  stats: {
    entitlements: {
      new?: number;
      redeemed?: number;
      terminated?: number;
    };
  };
};
