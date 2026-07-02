/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type AuditEventsSchema = {
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
};
