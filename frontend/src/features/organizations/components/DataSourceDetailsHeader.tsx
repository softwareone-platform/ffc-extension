import { Button } from "@swo/design-system/button";

import { DatasourceRead } from "~api/ffc-api-model/types.gen";
import { PageShell } from "~shared/components/page-shell";
import { useFixedT } from "~shared/hooks/useFixedT";
import { useModalToggle } from "~shared/hooks/useModalToggle";

import { useDataSourceApi } from "../api/useDataSourceApi";
import { DataSourceForceImportModal } from "../details/data-sources/force-import-modal/DataSourceForceImportModal";

type Props = {
  organizationId: string;
  dataSourceId: string;
  backUrl: string;
};

export function DataSourceDetailsHeader({
  organizationId,
  dataSourceId,
  backUrl,
}: Readonly<Props>) {
  const { data: entity, refetch } = useDataSourceApi(organizationId, dataSourceId);
  const forceImportModal = useModalToggle<DatasourceRead>({ onSuccess: refetch });
  const tDataSource = useFixedT("datasource");
  const title = <span>{entity?.datasource_id}</span>;

  return (
    <>
      <PageShell.Header
        backUrl={backUrl}
        title={title}
        subtitle={entity?.name ? `${entity.name}` : tDataSource("breadcrumb")}
        actions={
          <Button onClick={() => forceImportModal.open(entity)}>
            {tDataSource("force_import")}
          </Button>
        }
      />
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
