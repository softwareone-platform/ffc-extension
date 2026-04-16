import React from "react";
import { Button } from "@swo/design-system/button";
import "./modal.scss";
import { useMPTModal } from "@mpt-extension/sdk-react";

// const { auth, data } = useMPTContext();

export default () => {
  const { open, close } = useMPTModal();
  return (
    <>
      <div className="modal-header modal__container">
        <div className="modal-header-title">Create Organization</div>
      </div>
      <div className="modal__content modal__container">
        <p>
          Lorem ipsum dolor sit amet consectetur, adipisicing elit. Molestiae,
          pariatur quos? Aliquid ipsum voluptates doloribus, eum natus officiis!
          Voluptatibus quisquam facere dolore obcaecati nisi excepturi, officia
          aliquid eos? Culpa, recusandae?
        </p>
      </div>
      <div className="modal-actions modal__container">
        <div className="modal-actions__content">
          <Button type="secondary" onClick={() => close("cancel")}>
            Cancel
          </Button>
          <Button type="primary" onClick={() => close("save")}>Save</Button>
        </div>
      </div>
    </>
  );
};
