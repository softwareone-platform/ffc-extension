import { EmployeeRead } from "~api/ffc-api-model";

export type Employee = EmployeeRead;

export type EmployeeActions = "make_admin" | "delete" | "re-invite";
