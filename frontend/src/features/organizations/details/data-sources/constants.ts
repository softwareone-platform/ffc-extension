import { DatasourceType } from "~api/ffc-api-model";

/**
 * Datasource types for which a data import can be forced.
 * Tenant-level datasources are not importable on their own — their children are.
 */
export const FORCE_IMPORT_ENABLED_TYPES: ReadonlySet<DatasourceType> = new Set<DatasourceType>([
  "aws_cnr",
  "azure_cnr",
  "gcp_cnr",
]);

export function isForceImportEnabled(type: DatasourceType): boolean {
  return FORCE_IMPORT_ENABLED_TYPES.has(type);
}
