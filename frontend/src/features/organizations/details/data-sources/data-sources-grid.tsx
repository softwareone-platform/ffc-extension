import { Grid } from '@swo/design-system/grid';
import { DatasourceRead } from '@swo/ffc-api-model';
import { useGridConfig } from './data-sources-grid.config';

export function DataSourcesGrid({ organizationId }: { organizationId: string }) {
    const { silentRefresh, ...gridProps } = useGridConfig(organizationId);

    return <Grid<DatasourceRead> {...gridProps} />;
}
