import { Grid } from "@swo/design-system/grid";

import { DatasourceDetailRead, DatasourceDiscoveryItem } from "~api/ffc-api-model";

import { useGridConfig } from "./DiscoveryGrid.config";

export function DiscoveryGrid({ dataSource }: { readonly dataSource: DatasourceDetailRead }) {
  const { ...gridProps } = useGridConfig(dataSource?.discovery || []);

  return <Grid<DatasourceDiscoveryItem> {...gridProps} />;
}
