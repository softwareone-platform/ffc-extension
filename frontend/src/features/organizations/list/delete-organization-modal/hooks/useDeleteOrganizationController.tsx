import { useCallback, useState } from "react";

import { useMutation } from "@tanstack/react-query";
import { AxiosError } from "axios";

import { OrganizationRead } from "~api/ffc-api-model";
import { useOrganizationsApi } from "~features/organizations/api/useOrganizationsApi";
import { ModalCloseResult } from "~shared/components/modal/types";
import { useErrorDetails } from "~shared/hooks/useErrorDetails";

export type DeleteOrganizationModalControllerProps = {
  onClose?: (result?: ModalCloseResult) => void;
};

export function useDeleteOrganizationController({
  onClose,
}: DeleteOrganizationModalControllerProps) {
  const { deleteOrganization } = useOrganizationsApi();
  const [error, setError] = useState<string | null>(null);
  const { getErrorMessage } = useErrorDetails("organizations:delete_organization:errors");

  const handleCancel = useCallback((): void => {
    if (onClose) {
      setError(null);
      onClose();
    }
  }, [onClose]);

  const onError = useCallback(
    (err: AxiosError): void => {
      setError(getErrorMessage(err));
    },
    [getErrorMessage],
  );

  const onSuccess = useCallback((): void => {
    if (onClose) {
      setError(null);
      onClose({ success: true });
    }
  }, [onClose]);

  const { mutateAsync, isPending } = useMutation({
    mutationFn: (organizationId: string) => deleteOrganization(organizationId),
    onSuccess,
    onError,
  });

  const remove = async (organization: OrganizationRead) => {
    await mutateAsync(organization.id);
  };

  return { remove, error, isPending, handleCancel };
}
