/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type AccountUserReferenceWithAccount = {
  status: 'invited' | 'invitation-expired' | 'active' | 'deleted';
  id: string;
  created_at?: (string | null);
  joined_at?: (string | null);
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
};
