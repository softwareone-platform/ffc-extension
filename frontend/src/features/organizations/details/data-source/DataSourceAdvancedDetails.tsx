import { useParams } from "react-router-dom";

import { useDataSourceApi } from "~features/organizations/api/useDataSourceApi";
import { useFixedT } from "~shared/hooks/useFixedT";

import { BillingImport } from "./advanced/BillingImport";
import { Discovery } from "./advanced/Discovery";
import { MonitoringMetrics } from "./advanced/MonitoringMetrics";
import styles from "./DataSourceAdvancedDetails.module.scss";
import { DataSourceError } from "./DataSourceError";
import { LoadingDataSourceProperties } from "./properties/LoadingProperties";

export function DataSourceAdvancedDetails() {
  const tSharedDetails = useFixedT("shared:details");
  const { organizationId, dataSourceId } = useParams();
  const { data: dataSource, isLoading } = useDataSourceApi(organizationId, dataSourceId);

  if (isLoading) {
    return <LoadingDataSourceProperties title={tSharedDetails("billing_import")} />;
  }

  if (!dataSource) {
    return <DataSourceError />;
  }

  return (
    <>
      <div className={styles.advancedDetailsHead}>
        <BillingImport entity={dataSource} />
        <MonitoringMetrics entity={dataSource} />
      </div>
      <Discovery entity={dataSource} />
    </>
  );
}
