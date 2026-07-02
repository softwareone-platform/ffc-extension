/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type LimitOffsetPage_EntitlementRead_ = {
  items: Array<{
    name: string;
    affiliate_external_id: string;
    datasource_id: string;
    redeem_at?: (string | null);
    id: string;
    linked_datasource_id?: (string | null);
    linked_datasource_name?: (string | null);
    linked_datasource_type?: ('aws_cnr' | 'azure_cnr' | 'azure_tenant' | 'gcp_cnr' | 'unknown' | null);
    owner: {
      id: string;
      name: string;
      type: 'admin' | 'operations' | 'affiliate';
      integration: ('aws' | 'google' | 'microsoft' | 'softwareone' | null);
      /**
       * An external identifier for the account
       */
      external_id: string;
    };
    status: 'new' | 'active' | 'terminated' | 'deleted';
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
      redeemed?: ({
        at: string;
        by: {
          id: string;
          name: string;
          operations_external_id: string;
        };
      } | null);
      terminated?: ({
        at: string;
        by: ({
          id: string;
          type: 'user' | 'system';
          name: string;
        } | null);
      } | null);
    };
  }>;
  total: number;
  limit: (number | null);
  offset: number;
};
