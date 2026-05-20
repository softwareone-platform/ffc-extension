import { useParams } from 'react-router-dom';

import { UsersGrid } from './UsersGrid';

export function OrganizationUsers() {
    const { organizationId } = useParams();

    return <>{organizationId && <UsersGrid organizationId={organizationId}></UsersGrid>}</>;
}
