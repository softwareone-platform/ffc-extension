import { InlineNotification } from "@swo/design-system/notification";
import { NO_VALUE, useFormatDate } from "@swo/design-system/utils";

import { Organization } from "~features/organizations/api/model";
import { InlineErrorNotification } from "~shared/components/error/InlineErrorNotification";
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
  const formatDate = useFormatDate();

  const isDeletable = organization?.deletable_at
    ? new Date(organization.deletable_at) < new Date()
    : false;

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
      isSubmitDisabled={!isDeletable}
      submitButtonColor="danger"
    >
      <InlineErrorNotification error={error} />
      {!isDeletable && (
        <div className="organization-is-deletable-warning">
          <InlineNotification status="warning">
            <p>
              {tOrganization("not_deletable", {
                date: organization?.deletable_at
                  ? formatDate(organization?.deletable_at)
                  : NO_VALUE,
              })}
            </p>
          </InlineNotification>
        </div>
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
