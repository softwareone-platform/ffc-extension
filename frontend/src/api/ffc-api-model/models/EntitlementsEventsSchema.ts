/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type EntitlementsEventsSchema = {
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
  redeemed?: {
    at: string;
    by: {
      id: string;
      name: string;
      operations_external_id: string;
    };
  } | null;
  terminated?: {
    at: string;
    by: {
      id: string;
      type: "user" | "system";
      name: string;
    } | null;
  } | null;
};
