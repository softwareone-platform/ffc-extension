import { Grid } from "@swo/design-system/grid";
import { DatasourceRead } from "~api/ffc-api-model";

import { useGridConfig } from "./DataSourcesGrid.config";

export function DataSourcesGrid({ organizationId }: { organizationId: string }) {
  const { ...gridProps } = useGridConfig(organizationId);

  return <Grid<DatasourceRead> {...gridProps} />;
}
