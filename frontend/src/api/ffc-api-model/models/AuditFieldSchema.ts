/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
export type AuditFieldSchema = {
  at: string;
  by: {
    id: string;
    type: "user" | "system";
    name: string;
  } | null;
};
