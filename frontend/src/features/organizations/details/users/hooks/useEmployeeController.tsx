import { useCallback, useState } from "react";

import { useMutation } from "@tanstack/react-query";
import { AxiosError } from "axios";

import { Employee } from "~features/organizations/api/model";
import { useEmployeesApi } from "~features/organizations/api/useEmployeesApi";
import { ModalControllerProps } from "~shared/components/modal/types";
import { useErrorDetails } from "~shared/hooks/useErrorDetails";

export function useEmployeeController({ onClose }: ModalControllerProps = {}) {
  const [error, setError] = useState<string | null>(null);
  const { promoteToAdmin } = useEmployeesApi();
  const { getErrorMessage } = useErrorDetails("organizations:make_admin:errors");

  const cancel = useCallback((): void => {
    if (onClose) {
      onClose();
    }
  }, [onClose]);

  const onError = useCallback(
    (err: AxiosError): void => {
      setError(getErrorMessage(err));
    },
    [getErrorMessage],
  );

  const onSuccess = useCallback((): void => {
    if (onClose) {
      onClose({ success: true });
    }
  }, [onClose]);

  const { mutateAsync, isPending } = useMutation({
    mutationFn: ({ organizationId, employeeId }: { organizationId: string; employeeId: string }) =>
      promoteToAdmin(organizationId, employeeId),
    onSuccess,
    onError,
  });

  const makeAdmin = async ({
    organizationId,
    employee,
  }: {
    organizationId: string;
    employee: Employee;
  }) => {
    await mutateAsync({ organizationId: organizationId, employeeId: employee.id });
  };

  return { makeAdmin, error, isPending, cancel };
}
