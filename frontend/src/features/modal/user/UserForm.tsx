import { useCallback, useState } from "react";

import { useMutation } from "@tanstack/react-query";
import { AxiosError } from "axios";

import { Button } from "@swo/design-system/button";
import { InlineNotification } from "@swo/notification";

import { useMPTContext, useMPTModal } from "@mpt-extension/sdk-react";

import { ControlledInput } from "~shared/components/form/ControlledInput";
import { useFixedT } from "~shared/hooks/useFixedT";

import { useEmployeesApi } from "~features/organizations/api/useEmployeesApi";
import { ModalCancelButton } from "../shared/ModalCancelButton";
import { ModalEntryProps } from "../shared/defineModalEntry";
import { AddUserForm } from "./AddUserForm.Schema";
import { useAddUserForm } from "./hooks/useAddUserForm";

export const UserForm = ({ onClose }: ModalEntryProps = {}) => {
  const { close } = useMPTModal();
  const { data } = useMPTContext();
  const { addAdmin } = useEmployeesApi();
  const [error, setError] = useState<string | null>(null);
  const { handleSubmit, control } = useAddUserForm({
    email: "",
    display_name: "",
  });
  const tProperties = useFixedT("shared:properties");
  const tPlaceholders = useFixedT("shared:placeholders");
  const tErrors = useFixedT("organization:users:errors");
  const tUsers = useFixedT("organization:users");

  const handleCancel = useCallback((): void => {
    if (onClose) {
      onClose();
      return;
    }
    close("cancel");
  }, [onClose, close]);

  const onError = useCallback((error: AxiosError): void => {
    return setError(tErrors("add_admin_failed_with_code_" + (error.status || "unknown")));
  }, [tErrors]);
  const onSuccess = useCallback((): void => {
    if (onClose) {
      onClose({ success: true });
      return;
    }
    close({ success: true });
  }, [onClose, close]);

  const { mutateAsync, isPending } = useMutation({
    mutationFn: (formData: AddUserForm) => addAdmin(data.organizationId, formData),
    onSuccess: onSuccess,
    onError: onError,
  });

  const onSave = useCallback(
    async (formData: AddUserForm) => {
      await mutateAsync(formData);
    },
    [mutateAsync],
  );

  return (
    <form onSubmit={handleSubmit(onSave)}>
      <div className="modal__content modal__container">
        {error && (
          <div className="modal__error">
            <InlineNotification status="error" isToShowCloseButton={false} width="auto">
              {error}
            </InlineNotification>
          </div>
        )}

        <p>{tUsers("create_admin_info")}</p>
        <ControlledInput
          className="modal__input"
          control={control}
          name="email"
          type="default"
          isPreventAutocomplete={true}
          label={tProperties("email")}
          labelType="required"
          placeholder={tPlaceholders("email")}
        />
        <ControlledInput
          className="modal__input"
          control={control}
          name="display_name"
          type="default"
          isPreventAutocomplete={true}
          label={tProperties("display_name")}
          labelType="required"
          placeholder={tPlaceholders("display_name")}
        />
      </div>
      <div className="modal-actions modal__container">
        <div className="modal-actions__content">
          <ModalCancelButton onClick={handleCancel} isDisabled={isPending} />
          <Button type="primary" htmlType="submit" isBusy={isPending}>
            {tUsers("save")}
          </Button>
        </div>
      </div>
    </form>
  );
};
