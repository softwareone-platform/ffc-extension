import { InlineNotification } from "@swo/notification";

import { Employee } from "~features/organizations/api/model";
import { ModalCloseResult } from "~shared/components/modal/modalEntry";
import { StandaloneModal } from "~shared/components/modal/StandaloneModal";
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
    <StandaloneModal
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
      {error && (
        <InlineNotification status="error">
          {error
            .toString()
            .split("\n")
            .map((err, i) => (
              <p key={"error_" + i}>{err}</p>
            ))}
        </InlineNotification>
      )}
      <p>
        {tEntitlement("make_admin_warning_line1", {
          employeeId: employee?.id ?? "error",
          employeeName: employee?.display_name ?? "error",
          employeeEmail: employee?.email ?? "error",
        })}
      </p>
      <p>{tEntitlement("make_admin_warning_line2")}</p>
    </StandaloneModal>
  );
}
