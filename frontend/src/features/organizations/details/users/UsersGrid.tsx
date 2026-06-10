import { Button } from "@swo/design-system/button";
import { Grid } from "@swo/design-system/grid";
import { EmployeeRead } from "@swo/ffc-api-model";

import { useMPTModal } from "@mpt-extension/sdk-react";

import { useFixedT } from "~shared/hooks/useFixedT";

import { useGridConfig } from "./UsersGrid.config";

export function UsersGrid({ organizationId }: { organizationId: string }) {
  const { refresh, ...gridProps } = useGridConfig(organizationId);
  const { open } = useMPTModal();
  const tUsers = useFixedT("organization:users");

  return (
    <Grid<EmployeeRead> {...gridProps}>
      <Grid.Actions>
        <Button
          onClick={() =>
            open("finops.admin.create-user-modal", {
              context: { organizationId },
              onClose: (result) => {
                result.success && refresh();
              },
            })
          }
        >
          {tUsers("add")}
        </Button>
      </Grid.Actions>
    </Grid>
  );
}
