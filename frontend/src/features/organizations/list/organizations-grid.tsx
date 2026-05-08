import { Card } from '@swo/design-system/card';
import { Grid } from '@swo/design-system/grid';
import { OrganizationRead } from '@swo/ffc-api-model';
import { Entity } from '@swo/service';

import { useFixedT } from '~shared/hooks/use-fixed-t';

import { useGridConfig } from './organizations-grid.config';

export function OrganizationsGrid() {
    // const {auth, data} = useMPTContext();

    //TODO: proper translation name
    const tProperties = useFixedT('shared:grid:columns');
    const { silentRefresh, ...gridProps } = useGridConfig();

    return (
        <Card testId={'ffc-extension__organizations-grid'} title={tProperties('organizations')}>
            <Grid<Entity<OrganizationRead>> {...gridProps} />
        </Card>
    );
}
