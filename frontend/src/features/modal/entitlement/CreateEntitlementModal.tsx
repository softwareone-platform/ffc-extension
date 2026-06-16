import { useFixedT } from "~shared/hooks/useFixedT";

import { ModalEntryComponent } from "../shared/defineModalEntry";
import { ModalWidget } from "../shared/ModalWidget";
import { EntitlementsForm } from "./EntitlementsForm";

const CreateEntitlementModal: ModalEntryComponent = ({ onClose }) => {
  const tEntitlement = useFixedT("entitlement");

  return (
    <ModalWidget title={tEntitlement("add_entitlement")}>
      <EntitlementsForm onClose={onClose} />
    </ModalWidget>
  );
};

export default CreateEntitlementModal;
