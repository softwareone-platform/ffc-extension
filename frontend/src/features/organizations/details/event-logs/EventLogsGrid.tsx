import { Grid } from "@swo/design-system/grid";

import { OrganizationEventRead } from "~api/ffc-api-model";

import { useGridConfig } from "./EventLogsGrid.config";

export function EventLogsGrid({ organizationId }: { organizationId: string }) {
  const gridProps = useGridConfig(organizationId);

  return <Grid<OrganizationEventRead> {...gridProps} />;
}
