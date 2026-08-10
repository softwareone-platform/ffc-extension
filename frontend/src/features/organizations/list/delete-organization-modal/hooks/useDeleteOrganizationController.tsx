import { useCallback, useEffect, useState } from "react";

import { useMutation } from "@tanstack/react-query";
import { AxiosError } from "axios";

import { OrganizationRead } from "~api/ffc-api-model";
import { useOrganizationsApi } from "~features/organizations/api/useOrganizationsApi";
import { ModalCloseResult } from "~shared/components/modal/types";
import { useFixedT } from "~shared/hooks/useFixedT";

export type DeleteOrganizationModalControllerProps = {
  onClose?: (result?: ModalCloseResult) => void;
};

export function useDeleteOrganizationController({
  onClose,
}: DeleteOrganizationModalControllerProps) {
  const { deleteOrganization } = useOrganizationsApi();
  const [error, setError] = useState<string | null>(null);

  const tErrors = useFixedT("organizations:delete:errors");

  const handleCancel = useCallback((): void => {
    if (onClose) {
      setError(null);
      onClose();
    }
  }, [onClose]);

  const onError = useCallback(
    (err: AxiosError): void => {
      setError(tErrors("organization_delete_failed_with_code_" + (err.status || "unknown")));
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
    mutationFn: (organizationId: string) => deleteOrganization(organizationId),
    onSuccess,
    onError,
  });

  const remove = async (organization: OrganizationRead) => {
    await mutateAsync(organization.id);
  };

  return { remove, error, isPending, handleCancel };
}
