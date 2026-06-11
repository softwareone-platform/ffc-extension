import React, { useState } from "react";

import { Button } from "@swo/design-system/button";
import { Input } from "@swo/design-system/input";
import { Modal } from "@swo/design-system/modal";

export interface AddEntitlementsFormValues {
  name: string;
  description: string;
  contactEmail: string;
}

type Props = {
  isOpen: boolean;
  onClose: () => void;
  onSubmit?: (values: AddEntitlementsFormValues) => void;
};

const initialValues: AddEntitlementsFormValues = {
  name: "",
  description: "",
  contactEmail: "",
};

export const EntitlementsForm: React.FC<Props> = ({ isOpen, onClose, onSubmit }) => {
  const [values, setValues] = useState<AddEntitlementsFormValues>(initialValues);

  const update =
    (field: keyof AddEntitlementsFormValues) => (e: React.ChangeEvent<Element>) => {
      const target = e.target as HTMLInputElement | HTMLTextAreaElement;
      setValues((prev) => ({ ...prev, [field]: target.value }));
    };

  const handleClose = () => {
    setValues(initialValues);
    onClose();
  };

  const handleSubmit = () => {
    onSubmit?.(values);
    handleClose();
  };

  const isValid = values.name.trim().length > 0;

  return (
    <Modal
      title="Add entitlement"
      isOpen={isOpen}
      width={560}
      onClose={handleClose}
      actions={
        <>
          <Button type="text" onClick={handleClose}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} isDisabled={!isValid}>
            Add
          </Button>
        </>
      }
    >
      <div className="add-entitlement-form">
        <Input
          label="Name"
          placeholder="Acme Corp."
          value={values.name}
          isRequired
          onChange={update("name")}
          testId="add-entitlement-name"
        />
        <Input
          label="Description"
          placeholder="Short description"
          value={values.description}
          onChange={update("description")}
          testId="add-entitlement-description"
        />
        <Input
          label="Contact email"
          placeholder="admin@acme.com"
          value={values.contactEmail}
          onChange={update("contactEmail")}
          testId="add-entitlement-email"
        />
      </div>
    </Modal>
  );
};
