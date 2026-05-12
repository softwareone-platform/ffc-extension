import { Grid } from "@swo/design-system/grid";
import { DatasourceRead } from "@swo/ffc-api-model";
import { useGridConfig } from "./DataSources.Grid.config";
import { useOrganizationContext } from "../providers/OrganizationsProvider";

export function DataSourcesGrid({
  organizationId,
}: {
  organizationId: string;
}) {
  const { silentRefresh, ...gridProps } = useGridConfig(organizationId);
  return <Grid<DatasourceRead> {...gridProps} />;
}
