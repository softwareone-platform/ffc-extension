import { useParams } from 'react-router-dom';

import { DataSourcesGrid } from './DataSourcesGrid';

export function OrganizationDataSources() {
    const { organizationId } = useParams();

    return (
        <>{organizationId && <DataSourcesGrid organizationId={organizationId}></DataSourcesGrid>}</>
    );
}
