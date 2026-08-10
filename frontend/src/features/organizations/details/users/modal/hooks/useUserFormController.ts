import { useCallback, useState } from "react";

import { useMutation } from "@tanstack/react-query";
import { AxiosError } from "axios";

import { useMPTContext } from "@mpt-extension/sdk-react";

import { useEmployeesApi } from "~features/organizations/api/useEmployeesApi";
import { ModalCloseResult } from "~shared/components/modal/types";
import { useFixedT } from "~shared/hooks/useFixedT";

import { AddUserForm } from "../AddUserForm.Schema";
import { useAddUserForm } from "./useAddUserForm";

export function useUserFormController({
  onClose,
}: {
  onClose: (result?: ModalCloseResult) => void;
}) {
  const { data } = useMPTContext();
  const { addAdmin } = useEmployeesApi();
  const [error, setError] = useState<string | null>(null);
  const { handleSubmit, control, reset } = useAddUserForm({ email: "", display_name: "" });
  const tErrors = useFixedT("organization:users:errors");

  const handleCancel = useCallback((): void => {
    reset();
    onClose();
  }, [onClose, reset]);

  const onError = useCallback(
    (err: AxiosError): void => {
      setError(tErrors("add_admin_failed_with_code_" + (err.status || "unknown")));
    },
    [tErrors],
  );

  const onSuccess = useCallback((): void => {
    reset();
    onClose({ success: true });
  }, [onClose, reset]);

  const { mutateAsync, isPending } = useMutation({
    mutationFn: (formData: AddUserForm) => addAdmin(data.organizationId, formData),
    onSuccess,
    onError,
  });

  const submit = handleSubmit(async (formData: AddUserForm) => {
    await mutateAsync(formData);
  });

  return { control, error, isPending, submit, handleCancel };
}
