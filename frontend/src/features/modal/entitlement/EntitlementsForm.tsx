import { useCallback, useState } from "react";

import { useMutation } from "@tanstack/react-query";
import { AxiosError } from "axios";

import { Button } from "@swo/design-system/button";
import { InlineNotification } from "@swo/notification";

import { useMPTModal } from "@mpt-extension/sdk-react";

import { ControlledInput } from "~shared/components/form/ControlledInput";
import { useFixedT } from "~shared/hooks/useFixedT";

import { ModalCancelButton } from "../shared/ModalCancelButton";
import { ModalEntryProps } from "../shared/defineModalEntry";
import { AddEntitlementForm } from "./AddEntitlementForm.Schema";
import { useAddEntitlementForm } from "./hooks/useAddEntitlementForm";

export const EntitlementsForm = ({ onClose }: ModalEntryProps = {}) => {
  const { close } = useMPTModal();
  const [error, setError] = useState<string | null>(null);
  const { handleSubmit, control } = useAddEntitlementForm({
    name: "",
    description: "",
    contactEmail: "",
  });
  const tProperties = useFixedT("entitlement:properties");
  const tPlaceholders = useFixedT("entitlement:placeholders");
  const tErrors = useFixedT("entitlement:errors");
  const tEntitlement = useFixedT("entitlement");

  const handleCancel = useCallback((): void => {
    if (onClose) {
      onClose();
      return;
    }
    close("cancel");
  }, [onClose, close]);

  const onError = useCallback(
    (_error: AxiosError): void => {
      setError(tErrors("create_failed"));
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
    mutationFn: async (formData: AddEntitlementForm) => {
      // Placeholder for the real entitlement API call.
      console.log("[entitlements] add entitlement submitted", formData);
      return formData;
    },
    onSuccess,
    onError,
  });

  const onSave = useCallback(
    async (formData: AddEntitlementForm) => {
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

        <p>{tEntitlement("create_info")}</p>
        <ControlledInput
          className="modal__input"
          control={control}
          name="name"
          type="default"
          label={tProperties("name")}
          labelType="required"
          placeholder={tPlaceholders("name")}
        />
        <ControlledInput
          className="modal__input"
          control={control}
          name="description"
          type="default"
          label={tProperties("description")}
          placeholder={tPlaceholders("description")}
        />
        <ControlledInput
          className="modal__input"
          control={control}
          name="contactEmail"
          type="default"
          label={tProperties("contactEmail")}
          placeholder={tPlaceholders("contactEmail")}
        />
      </div>
      <div className="modal-actions modal__container">
        <div className="modal-actions__content">
          <ModalCancelButton onClick={handleCancel} isDisabled={isPending} />
          <Button type="primary" htmlType="submit" isBusy={isPending}>
            {tEntitlement("save")}
          </Button>
        </div>
      </div>
    </form>
  );
};
