import { useEffect } from "react";

import { OrganizationRead } from "~api/ffc-api-model";
import { useOrganizationsApi } from "~features/organizations/api/useOrganizationsApi";
import { ModalCloseResult } from "~shared/components/modal/types";
import { useBaseModalController } from "~shared/hooks/useBaseModalController";
import { useFixedT } from "~shared/hooks/useFixedT";

import { EditOrganizationForm } from "../EditOrganization.Schema";
import { useEditOrganizationForm } from "./useEditOrganizationForm";

export type EditOrganizationModalControllerProps = {
  organization: OrganizationRead | null;
  onClose?: (result?: ModalCloseResult) => void;
};

export function useOrganizationsController({
  onClose,
  organization,
}: EditOrganizationModalControllerProps) {
  const { editOrganization } = useOrganizationsApi();
  const { handleSubmit, control, setValue } = useEditOrganizationForm({
    name: "",
    operations_external_id: "",
    currency: "",
  });
  const tErrors = useFixedT("organizations:edit:errors");

  useEffect(() => {
    if (organization) {
      setValue("name", organization.name, {
        shouldValidate: true,
      });
      setValue("operations_external_id", organization.operations_external_id, {
        shouldValidate: true,
      });
      setValue("currency", organization.currency, {
        shouldValidate: true,
      });
    }
  }, [organization, setValue]);

  const { error, setError, isPending, mutateAsync, cancel } = useBaseModalController({
    namespace: "organizations:edit:errors",
    mutationFn: ({
      organizationId,
      formData,
    }: {
      organizationId: string;
      formData: EditOrganizationForm;
    }) => editOrganization(organizationId, formData),
    onClose,
  });

  const submit = handleSubmit(async (formData: EditOrganizationForm) => {
    // Checked before mutating so onError can't overwrite this message with a generic one.
    if (!organization) {
      setError(tErrors("organization_required"));
      return;
    }

    await mutateAsync({ organizationId: organization.id, formData });
  });

  return { submit, control, error, isPending, cancel };
}
