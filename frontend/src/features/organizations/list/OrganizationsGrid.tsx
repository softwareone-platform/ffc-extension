import { Card } from "@swo/design-system/card";
import { Grid } from "@swo/design-system/grid";
import { OrganizationRead } from "@swo/ffc-api-model";
import { Entity } from "@swo/service";

import { useFixedT } from "~shared/hooks/useFixedT";

import { useGridConfig } from "./OrganizationsGrid.config";

export function OrganizationsGrid() {
  const tProperties = useFixedT("shared:grid:columns");
  const { ...gridProps } = useGridConfig();

  return (
    <Card testId={"ffc-extension__organizations-grid"} title={tProperties("organizations")}>
      <Grid<Entity<OrganizationRead>> {...gridProps} />
    </Card>
  );
}
