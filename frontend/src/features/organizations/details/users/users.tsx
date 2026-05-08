import { useParams } from 'react-router-dom';
import { UsersGrid } from './users-grid';

export function OrganizationUsers() {
    const { organizationId } = useParams();

    return <>{organizationId && <UsersGrid organizationId={organizationId}></UsersGrid>}</>;
}
