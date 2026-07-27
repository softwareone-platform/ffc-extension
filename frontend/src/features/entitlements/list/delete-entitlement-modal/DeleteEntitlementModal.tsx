import { InlineNotification } from "@swo/notification";

import { Entitlement } from "~features/entitlements/api/model";
import { ModalCloseResult } from "~shared/components/modal/types";
import { Modal } from "~shared/components/modal/Modal";
import { useFixedT } from "~shared/hooks/useFixedT";

import { useEntitlementController } from "../hooks/useEntitlementsController";

type Props = {
  isOpen: boolean;
  onClose: (result?: ModalCloseResult) => void;
  className?: string;
  entitlement: Entitlement | null;
  onSuccess?: () => void;
};

export function DeleteEntitlementModal({
  isOpen,
  onClose,
  className,
  entitlement,
  onSuccess,
}: Readonly<Props>) {
  const tEntitlement = useFixedT("entitlements:delete_entitlement");
  const { cancel, remove, isPendingRemove, error } = useEntitlementController({ onClose });

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={tEntitlement("title")}
      className={className}
      onCancel={cancel}
      onSubmit={() => entitlement && remove(entitlement).then(() => onSuccess?.())}
      submitLabel={tEntitlement("delete")}
      isSubmitting={isPendingRemove}
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
        {tEntitlement("delete_entitlement_warning_line1", {
          entitlementId: entitlement?.id ?? "error",
        })}
      </p>
      <p>{tEntitlement("delete_entitlement_warning_line2")}</p>
    </Modal>
  );
}
