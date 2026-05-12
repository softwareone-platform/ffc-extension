import { Grid } from '@swo/design-system/grid';
import { EmployeeRead } from '@swo/ffc-api-model';

import { useGridConfig } from './UsersGrid.config';

export function UsersGrid({ organizationId }: { organizationId: string }) {
    const { silentRefresh, ...gridProps } = useGridConfig(organizationId);

    return <Grid<EmployeeRead> {...gridProps} />;
}
