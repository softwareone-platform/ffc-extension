import { Grid } from '@swo/design-system/grid';
import { EmployeeRead } from '@swo/ffc-api-model';
import { useFixedT } from '~shared/hooks/use-fixed-t';
import { useGridConfig } from './users-grid.config';

export function UsersGrid({ organizationId }: { organizationId: string }) {
    const tProperties = useFixedT('shared:grid:columns');
    const { silentRefresh, ...gridProps } = useGridConfig(organizationId);

    return <Grid<EmployeeRead> {...gridProps} />;
}
