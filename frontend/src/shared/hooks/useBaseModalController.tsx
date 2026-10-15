import { useCallback, useState } from "react";

import { MutationFunction, useMutation } from "@tanstack/react-query";
import { AxiosError } from "axios";

import { ModalCloseResult } from "~shared/components/modal/types";

import { useErrorDetails } from "./useErrorDetails";

export type BaseControllerOptions<TData, TVariables> = {
  namespace: string;
  mutationFn: MutationFunction<TData, TVariables>;
  onClose?: (result?: ModalCloseResult) => void;
  // Resets controller-specific state (e.g. form values) on cancel and on success.
  reset?: () => void;
};

export function useBaseModalController<TData = unknown, TVariables = void>({
  namespace,
  mutationFn,
  onClose,
  reset,
}: BaseControllerOptions<TData, TVariables>) {
  const [error, setError] = useState<string | null>(null);
  const { getErrorMessage } = useErrorDetails(namespace);

  const cancel = useCallback((): void => {
    reset?.();
    setError(null);
    onClose?.();
  }, [onClose, reset]);

  const onError = useCallback(
    (err: AxiosError): void => {
      setError(getErrorMessage(err));
    },
    [getErrorMessage],
  );

  const onSuccess = useCallback((): void => {
    reset?.();
    setError(null);
    onClose?.({ success: true });
  }, [onClose, reset]);

  const { mutate, mutateAsync, isPending } = useMutation<TData, AxiosError, TVariables>({
    mutationFn,
    onSuccess,
    onError,
  });

  return { error, setError, isPending, mutate, mutateAsync, cancel };
}
