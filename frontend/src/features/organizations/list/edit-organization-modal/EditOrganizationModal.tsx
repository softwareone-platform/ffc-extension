import { InlineNotification } from "@swo/notification";

import { OrganizationRead } from "~api/ffc-api-model/types.gen";
import { Modal } from "~shared/components/modal/Modal";
import { ModalCloseResult } from "~shared/components/modal/types";
import { useFixedT } from "~shared/hooks/useFixedT";

import { EditOrganizationFormFields } from "./EditOrganizationFormFields";
import { useOrganizationsController } from "./hooks/useOrganizationsController";

import "./EditOrganizationModal.scss";

type Props = {
  isOpen: boolean;
  onClose: (result?: ModalCloseResult) => void;
  className?: string;
  organization: OrganizationRead | null;
  onSuccess?: () => void;
};

export function EditOrganizationModal({
  isOpen,
  onClose,
  className,
  organization,
  onSuccess,
}: Readonly<Props>) {
  const tOrganization = useFixedT("organizations:edit");
  const { handleCancel, submit, isPending, error, control } = useOrganizationsController({
    onClose,
    organization,
  });

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={tOrganization("title")}
      className={className}
      onCancel={handleCancel}
      onSubmit={() => submit()}
      submitLabel={tOrganization("save")}
      isSubmitting={isPending}
      submitButtonColor="primary"
    >
      <form onSubmit={submit}>
        <EditOrganizationFormFields control={control} error={error} />
      </form>
    </Modal>
  );
}
