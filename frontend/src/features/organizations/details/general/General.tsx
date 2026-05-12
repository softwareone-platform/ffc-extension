import { useParams } from 'react-router-dom';

import { useOrganizationDetailsApi } from '~organizations/api';

export function OrganizationGeneralDetails() {
    const { organizationId } = useParams();
    const { data: entity } = useOrganizationDetailsApi(organizationId);

    return (
        <>
            <h1>Organization details</h1>
            <p>
                Top nav {organizationId} {entity?.name}
            </p>
            <p>This is where the details of the organization would be displayed.</p>
        </>
    );
}
