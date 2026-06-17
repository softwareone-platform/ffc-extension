import { useCallback, useState } from "react";

import { useMutation } from "@tanstack/react-query";
import { AxiosError } from "axios";

import { useMPTModal } from "@mpt-extension/sdk-react";

import { useFixedT } from "~shared/hooks/useFixedT";

import { ModalEntryProps } from "../../shared/modalEntry";
import { AddEntitlementForm } from "../AddEntitlementForm.Schema";
import { useAddEntitlementForm } from "./useAddEntitlementForm";

export function useEntitlementFormController({ onClose }: ModalEntryProps = {}) {
  const { close } = useMPTModal();
  const [error, setError] = useState<string | null>(null);
  const { handleSubmit, control } = useAddEntitlementForm({
    name: "",
    description: "",
    contactEmail: "",
  });
  const tErrors = useFixedT("entitlement:errors");

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
      console.log("[entitlements] add entitlement submitted", formData);
      return formData;
    },
    onSuccess,
    onError,
  });

  const submit = handleSubmit(async (formData: AddEntitlementForm) => {
    await mutateAsync(formData);
  });

  return { control, error, isPending, submit, handleCancel };
}
