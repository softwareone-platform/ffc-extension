import { PageShell } from "~shared/components/page-shell";

import { useDataSourceApi } from "../api/useDataSourceApi";

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
  const { data: entity } = useDataSourceApi(organizationId, dataSourceId);

  const title = <span>{entity?.datasource_id}</span>;

  return (
    <PageShell.Header
      backUrl={backUrl}
      title={title}
      subtitle={entity?.name ? `${entity.name}` : "Data source details"}
    />
  );
}
