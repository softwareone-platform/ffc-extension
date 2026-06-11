import { useMPTModal } from "@mpt-extension/sdk-react";

import { ModalWidget } from "../shared/ModalWidget";
import { EntitlementsForm } from "./EntitlementsForm";

export default () => {
  const { close } = useMPTModal();

  return (
    <ModalWidget title="Add entitlement">
      <EntitlementsForm
        isOpen={true}
        onClose={() => close("cancel")}
        onSubmit={(values) => {
          console.log("[entitlements] add entitlement submitted", values);
          close({ success: true });
        }}
      />
    </ModalWidget>
  );
};
