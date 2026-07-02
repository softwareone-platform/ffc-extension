/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type Me = {
  account: {
    id: string;
    name: string;
    type: 'admin' | 'operations' | 'affiliate';
    integration: ('aws' | 'google' | 'microsoft' | 'softwareone' | null);
    /**
     * An external identifier for the account
     */
    external_id: string;
  };
  system: ({
    id: string;
    name: string;
    external_id: string;
  } | null);
  user: ({
    name: string;
    external_id: string;
    email: string;
    id: string;
  } | null);
};
