import { Button } from "@swo/design-system/button";
import { Card } from "@swo/design-system/card";
import { Grid } from "@swo/design-system/grid";

import { useMPTModal } from "@mpt-extension/sdk-react";

import { useFixedT } from "~shared/hooks/useFixedT";

import { Entitlement } from "../api/model";
import { useGridConfig } from "./EntitlementsGrid.config";

export function EntitlementsGrid() {
  const tProperties = useFixedT("shared:grid:columns");
  const tActions = useFixedT("shared:grid:actions");
  const { refresh, ...gridProps } = useGridConfig();
  const { open } = useMPTModal();

  return (
    <Card testId={"ffc-extension__entitlements-grid"} title={tProperties("entitlements")}>
      <Grid<Entitlement> {...gridProps}>
        <Grid.Actions>
          <Button
            onClick={() =>
              open("finops.admin.create-entitlement-modal", {
                context: {},
                onClose: (result) => {
                  result.entitlementCreated && refresh();
                },
              })
            }
          >
            {tActions("add")}
          </Button>
        </Grid.Actions>
      </Grid>
    </Card>
  );
}
