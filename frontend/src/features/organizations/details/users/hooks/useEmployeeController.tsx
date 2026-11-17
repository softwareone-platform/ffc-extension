import { Employee } from "~features/organizations/api/model";
import { useEmployeesApi } from "~features/organizations/api/useEmployeesApi";
import { ModalControllerProps } from "~shared/components/modal/types";
import { useBaseModalController } from "~shared/hooks/useBaseModalController";

export function useEmployeeController({ onClose }: ModalControllerProps = {}) {
  const { promoteToAdmin } = useEmployeesApi();
  const { error, isPending, mutateAsync, cancel } = useBaseModalController({
    namespace: "organizations:make_admin:errors",
    mutationFn: ({ organizationId, employeeId }: { organizationId: string; employeeId: string }) =>
      promoteToAdmin(organizationId, employeeId),
    onClose,
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
