import { useCallback, useState } from "react";

import { useMutation } from "@tanstack/react-query";
import { AxiosError } from "axios";

import { useEmployeesApi } from "~features/organizations/api/useEmployeesApi";
import { ModalCloseResult } from "~shared/components/modal/types";
import { useErrorDetails } from "~shared/hooks/useErrorDetails";

import { AddUserForm } from "../AddUserForm.Schema";
import { useAddUserForm } from "./useAddUserForm";

export function useUserFormController({
  organizationId,
  onClose,
}: {
  organizationId: string;
  onClose: (result?: ModalCloseResult) => void;
}) {
  const { addAdmin } = useEmployeesApi();
  const [error, setError] = useState<string | null>(null);
  const { handleSubmit, control, reset } = useAddUserForm({ email: "", display_name: "" });
  const { getErrorMessage } = useErrorDetails("organization:users:errors");
  const handleCancel = useCallback((): void => {
    reset();
    setError("");
    onClose();
  }, [onClose, reset]);

  const onError = useCallback(
    (err: AxiosError): void => {
      setError(getErrorMessage(err));
    },
    [getErrorMessage],
  );

  const onSuccess = useCallback((): void => {
    reset();
    onClose({ success: true });
  }, [onClose, reset]);

  const { mutateAsync, isPending } = useMutation({
    mutationFn: (formData: AddUserForm) => addAdmin(organizationId, formData),
    onSuccess,
    onError,
  });

  const submit = handleSubmit(async (formData: AddUserForm) => {
    await mutateAsync(formData);
  });

  return { control, error, isPending, submit, handleCancel };
}
