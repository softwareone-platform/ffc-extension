/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type AccountReference = {
  id: string;
  name: string;
  type: "admin" | "operations" | "affiliate";
  integration: "aws" | "google" | "microsoft" | "softwareone" | null;
  /**
   * An external identifier for the account
   */
  external_id: string;
};
