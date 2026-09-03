import { InlineNotification } from "@swo/design-system/notification";

import { Organization } from "~features/organizations/api/model";
import { Modal } from "~shared/components/modal/Modal";
import { ModalCloseResult } from "~shared/components/modal/types";
import { useFixedT } from "~shared/hooks/useFixedT";

import { useDeleteOrganizationController } from "./hooks/useDeleteOrganizationController";

type Props = {
  isOpen: boolean;
  onClose: (result?: ModalCloseResult) => void;
  className?: string;
  organization: Organization | null;
  onSuccess?: () => void;
};

export function DeleteOrganizationModal({
  isOpen,
  onClose,
  className,
  organization,
  onSuccess,
}: Readonly<Props>) {
  const tOrganization = useFixedT("organizations:delete_organization");
  const { handleCancel, remove, isPending, error } = useDeleteOrganizationController({ onClose });

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={tOrganization("title")}
      className={className}
      onCancel={handleCancel}
      onSubmit={() => organization && remove(organization).then(() => onSuccess?.())}
      submitLabel={tOrganization("delete")}
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
        {tOrganization("delete_organization_warning_line1", {
          organizationId: organization?.id ?? "error",
          organizationName: organization?.name ?? "error",
        })}
      </p>
      <p>{tOrganization("delete_organization_warning_line2")}</p>
    </Modal>
  );
}
