import { useParams } from "react-router-dom";
import { UsersGrid } from "./Users.Grid";

export function OrganizationUsers() {
  const { organizationId } = useParams();

  return (
    <>
      {organizationId && (
        <UsersGrid organizationId={organizationId}></UsersGrid>
      )}
    </>
  );
}
