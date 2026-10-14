import { OrganizationRead } from "~api/ffc-api-model";
import { useOrganizationsApi } from "~features/organizations/api/useOrganizationsApi";
import { ModalCloseResult } from "~shared/components/modal/types";
import { useBaseModalController } from "~shared/hooks/useBaseModalController";

export type DeleteOrganizationModalControllerProps = {
  onClose?: (result?: ModalCloseResult) => void;
};

export function useDeleteOrganizationController({
  onClose,
}: DeleteOrganizationModalControllerProps) {
  const { deleteOrganization } = useOrganizationsApi();
  const { error, isPending, mutateAsync, cancel } = useBaseModalController({
    namespace: "organizations:delete_organization:errors",
    mutationFn: (organizationId: string) => deleteOrganization(organizationId),
    onClose,
  });

  const remove = async (organization: OrganizationRead) => {
    await mutateAsync(organization.id);
  };

  return { remove, error, isPending, cancel };
}
