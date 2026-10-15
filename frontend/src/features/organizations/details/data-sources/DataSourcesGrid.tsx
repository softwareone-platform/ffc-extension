import { Grid } from "@swo/design-system/grid";

import { DatasourceRead } from "~api/ffc-api-model";
import { DatasourceAction } from "~features/organizations/api/model";
import { useModalToggle } from "~shared/hooks/useModalToggle";

import { useGridConfig } from "./DataSourcesGrid.config";
import { DataSourceForceImportModal } from "./force-import-modal/DataSourceForceImportModal";

export function DataSourcesGrid({ organizationId }: { readonly organizationId: string }) {
  const { refresh, ...gridProps } = useGridConfig(organizationId, onAction);
  const forceImportModal = useModalToggle<DatasourceRead>({ onSuccess: refresh });

  function onAction(action: DatasourceAction, item: DatasourceRead) {
    if (action === "force_import") {
      forceImportModal.open(item);
    }
  }

  return (
    <>
      <Grid<DatasourceRead> {...gridProps} />
      <DataSourceForceImportModal
        className="force-import-modal"
        isOpen={forceImportModal.isOpen}
        onClose={forceImportModal.close}
        datasource={forceImportModal.data}
        organizationId={organizationId}
      />
    </>
  );
}
