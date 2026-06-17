import { Button } from "@swo/design-system/button";

import { useFixedT } from "~shared/hooks/useFixedT";

import { ModalCancelButton } from "../shared/ModalCancelButton";
import { ModalEntryComponent } from "../shared/modalEntry";
import { ModalWidget } from "../shared/ModalWidget";
import { EntitlementsFormFields } from "./EntitlementsFormFields";
import { useEntitlementFormController } from "./hooks/useEntitlementFormController";

const CreateEntitlementEntryModal: ModalEntryComponent = ({ onClose }) => {
  const tEntitlement = useFixedT("entitlement");
  const { control, error, isPending, submit, handleCancel } = useEntitlementFormController({ onClose });

  return (
    <ModalWidget title={tEntitlement("add_entitlement")}>
      <form onSubmit={submit}>
        <EntitlementsFormFields control={control} error={error} />
        <div className="modal-actions modal__container">
          <div className="modal-actions__content">
            <ModalCancelButton onClick={handleCancel} isDisabled={isPending} />
            <Button type="primary" htmlType="submit" isBusy={isPending}>
              {tEntitlement("save")}
            </Button>
          </div>
        </div>
      </form>
    </ModalWidget>
  );
};

export default CreateEntitlementEntryModal;
