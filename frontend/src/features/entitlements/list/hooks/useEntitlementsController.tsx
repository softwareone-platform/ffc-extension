import { useCallback, useState } from "react";

import { useMutation } from "@tanstack/react-query";
import { AxiosError } from "axios";

import { Entitlement } from "~features/entitlements/api/model";
import { useEntitlementsApi } from "~features/entitlements/api/useEntitlementsApi";
import { ModalControllerProps } from "~shared/components/modal/types";
import { useFixedT } from "~shared/hooks/useFixedT";

export function useEntitlementController({ onClose }: ModalControllerProps = {}) {
  const { terminateEntitlement, deleteEntitlement } = useEntitlementsApi();
  const [error, setError] = useState<string | null>(null);
  const tErrors = useFixedT("entitlements:terminate:errors");

  const cancel = useCallback((): void => {
    if (onClose) {
      setError(null);
      onClose();
    }
  }, [onClose]);

  const onError = useCallback(
    (err: AxiosError): void => {
      setError(tErrors("terminate_entitlement_failed_with_code_" + (err.status || "unknown")));
    },
    [tErrors],
  );

  const onSuccess = useCallback((): void => {
    if (onClose) {
      setError(null);
      onClose({ success: true });
    }
  }, [onClose]);

  const { mutateAsync: mutateTerminate, isPending: isPendingTerminate } = useMutation({
    mutationFn: (entitlementId: string) => terminateEntitlement(entitlementId),
    onSuccess,
    onError,
  });

  const terminate = async (entitlement: Entitlement) => {
    await mutateTerminate(entitlement.id);
  };

  const { mutateAsync: mutateRemove, isPending: isPendingRemove } = useMutation({
    mutationFn: (entitlementId: string) => deleteEntitlement(entitlementId),
    onSuccess,
    onError,
  });

  const remove = async (entitlement: Entitlement) => {
    await mutateRemove(entitlement.id);
  };

  return { terminate, remove, error, isPendingTerminate, isPendingRemove, cancel };
}
