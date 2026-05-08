import { DataSourcesGrid } from "./DataSources.Grid";
import { useParams } from "react-router-dom";

export function OrganizationDataSources() {
  const { organizationId } = useParams();

  return (
    <>
      {organizationId && (
        <DataSourcesGrid organizationId={organizationId}></DataSourcesGrid>
      )}
    </>
  );
}
