import { Card } from "@swo/design-system/card";
import { Grid } from "@swo/design-system/grid";

import { useGridConfig } from "./AgreementsGrid.config";
import { Agreement } from "./agreements.mock";

import "./AgreementsPage.scss";

export function AgreementsPage() {
  const gridProps = useGridConfig();

  return (
    <Card className="adobe-agreements">
      <Grid<Agreement> {...gridProps} />
    </Card>
  );
}
