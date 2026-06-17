import { useCallback, useState } from "react";

import { useMutation } from "@tanstack/react-query";
import { AxiosError } from "axios";

import { useMPTContext, useMPTModal } from "@mpt-extension/sdk-react";

import { useFixedT } from "~shared/hooks/useFixedT";

import { useEmployeesApi } from "~features/organizations/api/useEmployeesApi";
import { ModalEntryProps } from "../../shared/modalEntry";
import { AddUserForm } from "../AddUserForm.Schema";
import { useAddUserForm } from "./useAddUserForm";

export function useUserFormController({ onClose }: ModalEntryProps = {}) {
  const { close } = useMPTModal();
  const { data } = useMPTContext();
  const { addAdmin } = useEmployeesApi();
  const [error, setError] = useState<string | null>(null);
  const { handleSubmit, control } = useAddUserForm({ email: "", display_name: "" });
  const tErrors = useFixedT("organization:users:errors");

  const handleCancel = useCallback((): void => {
    if (onClose) {
      onClose();
      return;
    }
    close("cancel");
  }, [onClose, close]);

  const onError = useCallback(
    (err: AxiosError): void => {
      setError(tErrors("add_admin_failed_with_code_" + (err.status || "unknown")));
    },
    [tErrors],
  );

  const onSuccess = useCallback((): void => {
    if (onClose) {
      onClose({ success: true });
      return;
    }
    close({ success: true });
  }, [onClose, close]);

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
