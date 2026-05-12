import { Card } from '@swo/design-system/card';
import { Entity } from '@swo/service';
import { Grid } from '@swo/design-system/grid';
import { EntitlementRead, OrganizationRead } from '@swo/ffc-api-model';
import { useFixedT } from '../../../shared/hooks/useFixedT';
import { useGridConfig } from './Entitlements.Grid.config';
// import '../../../styles.scss';

export function EntitlementsGrid() {
  // const {auth, data} = useMPTContext();

  //TODO: proper translation name
  const tProperties = useFixedT("shared:grid:columns");
  const { silentRefresh, ...gridProps } = useGridConfig();

  return (
    <Card
      testId={"ffc-extension__entitlements-grid"}
      title={tProperties("entitlements")}
    >
      <Grid<EntitlementRead> {...gridProps} />
    </Card>
  );
}
