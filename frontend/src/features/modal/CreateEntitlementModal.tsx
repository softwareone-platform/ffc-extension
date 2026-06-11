import "./ModalWidget.scss";

import { useMPTModal } from "@mpt-extension/sdk-react";

import { AddEntitlementsModal } from "~features/organizations/components/AddEntitlementsModal";

export default () => {
  const { close } = useMPTModal();

  return (
    <div className="modal">
      <div className="modal-header modal__container">
        <div className="modal-header-title">Add entitlement</div>
      </div>
      <AddEntitlementsModal
        isOpen={true}
        onClose={() => close("cancel")}
        onSubmit={(values) => {
          console.log("[entitlements] add entitlement submitted", values);
          close({ success: true });
        }}
      />
    </div>
  );
};
