import { useEmployeesApi } from "~features/organizations/api/useEmployeesApi";
import { ModalCloseResult } from "~shared/components/modal/types";
import { useBaseModalController } from "~shared/hooks/useBaseModalController";

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
  const { handleSubmit, control, reset } = useAddUserForm({ email: "", display_name: "" });
  const { error, isPending, mutateAsync, cancel } = useBaseModalController({
    namespace: "organization:users:errors",
    mutationFn: (formData: AddUserForm) => addAdmin(organizationId, formData),
    onClose,
    reset,
  });

  const submit = handleSubmit(async (formData: AddUserForm) => {
    await mutateAsync(formData);
  });

  return { control, error, isPending, submit, cancel };
}
