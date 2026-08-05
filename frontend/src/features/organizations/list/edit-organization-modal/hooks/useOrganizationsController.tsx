import { useCallback, useEffect, useState } from "react";

import { useMutation } from "@tanstack/react-query";
import { AxiosError } from "axios";

import { OrganizationRead } from "~api/ffc-api-model";
import { useOrganizationsApi } from "~features/organizations/api/useOrganizationsApi";
import { ModalCloseResult } from "~shared/components/modal/types";
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
  const [error, setError] = useState<string | null>(null);
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

  const handleCancel = useCallback((): void => {
    if (onClose) {
      setError(null);
      onClose();
    }
  }, [onClose]);

  const onError = useCallback(
    (err: AxiosError): void => {
      setError(tErrors("organization_edit_failed_with_code_" + (err.status || "unknown")));
    },
    [tErrors],
  );

  const onSuccess = useCallback((): void => {
    if (onClose) {
      setError(null);
      onClose({ success: true });
    }
  }, [onClose]);

  const { mutateAsync, isPending } = useMutation({
    mutationFn: (formData: EditOrganizationForm) => {
      if (!organization) {
        setError(tErrors("organization_required"));
        return Promise.reject(new Error("Organization is required"));
      }

      return editOrganization(organization.id, formData);
    },
    onSuccess,
    onError,
  });

  const submit = handleSubmit(async (formData: EditOrganizationForm) => {
    await mutateAsync(formData);
  });

  return { submit, control, error, isPending, handleCancel };
}
