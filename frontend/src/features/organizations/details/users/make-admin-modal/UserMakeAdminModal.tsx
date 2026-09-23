import { Employee } from "~features/organizations/api/model";
import { InlineErrorNotification } from "~shared/components/error/InlineErrorNotification";
import { Modal } from "~shared/components/modal/Modal";
import { ModalCloseResult } from "~shared/components/modal/types";
import { useFixedT } from "~shared/hooks/useFixedT";

import { useEmployeeController } from "../hooks/useEmployeeController";

type Props = {
  isOpen: boolean;
  onClose: (result?: ModalCloseResult) => void;
  className?: string;
  employee: Employee | null;
  organizationId: string | null;
  onSuccess?: () => void;
};

export function UserMakeAdminModal({
  isOpen,
  onClose,
  className,
  employee,
  organizationId,
  onSuccess,
}: Readonly<Props>) {
  const tEntitlement = useFixedT("organizations:make_admin");
  const { cancel, makeAdmin, isPending, error } = useEmployeeController({ onClose });

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={tEntitlement("title")}
      className={className}
      onCancel={cancel}
      onSubmit={() =>
        employee &&
        organizationId &&
        makeAdmin({ organizationId, employee }).then(() => onSuccess?.())
      }
      submitLabel={tEntitlement("promote_to_admin")}
      isSubmitting={isPending}
      submitButtonColor="danger"
    >
      <InlineErrorNotification error={error} />
      <p>
        {tEntitlement("make_admin_warning_line1", {
          employeeId: employee?.id ?? "error",
          employeeName: employee?.display_name ?? "error",
          employeeEmail: employee?.email ?? "error",
        })}
      </p>
      <p>{tEntitlement("make_admin_warning_line2")}</p>
    </Modal>
  );
}
