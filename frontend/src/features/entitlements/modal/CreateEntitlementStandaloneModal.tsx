import { useFixedT } from "~shared/hooks/useFixedT";

import { ModalCloseResult } from "~shared/components/modal/modalEntry";
import { StandaloneModal } from "~shared/components/modal/StandaloneModal";
import { EntitlementsFormFields } from "./EntitlementsFormFields";
import { useEntitlementFormController } from "./hooks/useEntitlementFormController";

type Props = {
  isOpen: boolean;
  onClose: (result?: ModalCloseResult) => void;
};

export function CreateEntitlementStandaloneModal({ isOpen, onClose }: Readonly<Props>) {
  const tEntitlement = useFixedT("entitlement");
  const { control, error, isPending, submit, handleCancel } = useEntitlementFormController({
    onClose,
  });

  return (
    <StandaloneModal
      isOpen={isOpen}
      onClose={onClose}
      title={tEntitlement("add_entitlement")}
      onCancel={handleCancel}
      onSubmit={() => submit()}
      submitLabel={tEntitlement("save")}
      isSubmitting={isPending}
    >
      <form onSubmit={submit}>
        <EntitlementsFormFields control={control} error={error} />
      </form>
    </StandaloneModal>
  );
}
