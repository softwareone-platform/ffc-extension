import { EmployeeRead, OrganizationRead } from "~api/ffc-api-model";

export type Employee = EmployeeRead;

export type EmployeeActions = "make_admin" | "delete" | "re-invite";

export type Organization = OrganizationRead;

export type OrganizationAction = "edit" | "activate" | "terminate" | "delete";
