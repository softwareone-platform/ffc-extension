import { useParams } from "react-router-dom";

import { useDataSourceApi } from "~features/organizations/api/useDataSourceApi";

import { DataSourceError } from "./DataSourceError";
import { AWSDataSourceProperties } from "./properties/AWSProperties";
import { AzureDataSourceProperties } from "./properties/AzureProperties";
import { GCPDataSourceProperties } from "./properties/GCPProperties";
import { LoadingDataSourceProperties } from "./properties/LoadingProperties";
import { UnknownDataSourceProperties } from "./properties/UnknownProperties";

export function DataSourceDetails() {
  const { organizationId, dataSourceId } = useParams();
  const { data: entity, isLoading } = useDataSourceApi(organizationId, dataSourceId);

  if (isLoading) {
    return <LoadingDataSourceProperties />;
  }

  if (!entity) {
    return <DataSourceError />;
  }

  switch (entity.type) {
    case "aws_cnr":
      return <AWSDataSourceProperties entity={entity} />;
    case "azure_tenant":
    case "azure_cnr":
      return <AzureDataSourceProperties entity={entity} />;
    case "gcp_cnr":
    case "gcp_tenant":
      return <GCPDataSourceProperties entity={entity} />;
    default:
      return <UnknownDataSourceProperties entity={entity} />;
  }
}
