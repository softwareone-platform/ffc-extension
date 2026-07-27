import { InlineNotification } from "@swo/notification";

import { Entitlement } from "~features/entitlements/api/model";
import { ModalCloseResult } from "~shared/components/modal/types";
import { StandaloneModal } from "~shared/components/modal/StandaloneModal";
import { useFixedT } from "~shared/hooks/useFixedT";

import { useEntitlementController } from "../hooks/useEntitlementsController";

type Props = {
  isOpen: boolean;
  onClose: (result?: ModalCloseResult) => void;
  className?: string;
  entitlement: Entitlement | null;
  onSuccess?: () => void;
};

export function TerminateEntitlementModal({
  isOpen,
  onClose,
  className,
  entitlement,
  onSuccess,
}: Readonly<Props>) {
  const tEntitlement = useFixedT("entitlements:terminate_entitlement");
  const { cancel, terminate, isPendingTerminate, error } = useEntitlementController({ onClose });

  return (
    <StandaloneModal
      isOpen={isOpen}
      onClose={onClose}
      title={tEntitlement("title")}
      className={className}
      onCancel={cancel}
      onSubmit={() => entitlement && terminate(entitlement).then(() => onSuccess?.())}
      submitLabel={tEntitlement("terminate")}
      isSubmitting={isPendingTerminate}
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
        {tEntitlement("terminate_entitlement_warning_line1", {
          entitlementId: entitlement?.id ?? "error",
        })}
      </p>
      <p>{tEntitlement("terminate_entitlement_warning_line2")}</p>
      <p>{tEntitlement("terminate_entitlement_warning_line3")}</p>
    </StandaloneModal>
  );
}
