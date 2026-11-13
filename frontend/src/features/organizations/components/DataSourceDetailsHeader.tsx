import { Button } from "@swo/design-system/button";

import { DatasourceRead } from "~api/ffc-api-model/types.gen";
import { PageShell } from "~shared/components/page-shell";
import { useFixedT } from "~shared/hooks/useFixedT";
import { useModalToggle } from "~shared/hooks/useModalToggle";
import { useUserRole } from "~shared/hooks/useUserRole";

import { useDataSourceApi } from "../api/useDataSourceApi";
import { isForceImportEnabled } from "../details/data-sources/constants";
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
  const { data: entity, refetch, isLoading } = useDataSourceApi(organizationId, dataSourceId);
  const forceImportModal = useModalToggle<DatasourceRead>({ onSuccess: refetch });
  const tDataSource = useFixedT("datasource");
  const title = <span>{entity?.datasource_id}</span>;
  const { role } = useUserRole();
  const isNotEnabledByType = entity?.type !== undefined && !isForceImportEnabled(entity?.type);

  return (
    <>
      <PageShell.Header
        backUrl={backUrl}
        title={title}
        subtitle={entity?.name ? `${entity.name}` : tDataSource("breadcrumb")}
        actions={
          role === "admin" && (
            <Button
              onClick={() => forceImportModal.open(entity)}
              isDisabled={entity?.type === undefined || isNotEnabledByType || isLoading}
            >
              {tDataSource("force_import")}
            </Button>
          )
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
