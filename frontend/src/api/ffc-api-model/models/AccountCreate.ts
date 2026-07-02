/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type AccountCreate = {
  /**
   * The name of the account
   */
  name: string;
  /**
   * An external identifier for the account
   */
  external_id: string;
  type: 'admin' | 'operations' | 'affiliate';
  integration?: ('aws' | 'google' | 'microsoft' | 'softwareone' | null);
};
