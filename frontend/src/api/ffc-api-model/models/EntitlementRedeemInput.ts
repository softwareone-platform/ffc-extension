/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type EntitlementRedeemInput = {
  organization: {
    id: string;
  };
  datasource: {
    id: string;
    name: string;
    type: 'aws_cnr' | 'azure_cnr' | 'azure_tenant' | 'gcp_cnr' | 'unknown';
  };
};
