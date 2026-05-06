import React, { useState } from 'react';
import { Button } from '@swo/design-system/button';
import { Modal } from '@swo/design-system/modal';
import { Input } from '@swo/design-system/input';

export interface AddOrganizationFormValues {
    name: string;
    description: string;
    contactEmail: string;
}

interface AddOrganizationModalProps {
    isOpen: boolean;
    onClose: () => void;
    onSubmit?: (values: AddOrganizationFormValues) => void;
}

const initialValues: AddOrganizationFormValues = {
    name: '',
    description: '',
    contactEmail: '',
};

export const AddOrganizationModal: React.FC<AddOrganizationModalProps> = ({
    isOpen,
    onClose,
    onSubmit,
}) => {
    const [values, setValues] = useState<AddOrganizationFormValues>(initialValues);

    const update =
        (field: keyof AddOrganizationFormValues) =>
        (e: React.ChangeEvent<Element>) => {
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
            title="Add organization"
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
            <div className="add-organization-form">
                <Input
                    label="Name"
                    placeholder="Acme Corp."
                    value={values.name}
                    isRequired
                    onChange={update('name')}
                    testId="add-organization-name"
                />
                <Input
                    label="Description"
                    placeholder="Short description"
                    value={values.description}
                    onChange={update('description')}
                    testId="add-organization-description"
                />
                <Input
                    label="Contact email"
                    placeholder="admin@acme.com"
                    value={values.contactEmail}
                    onChange={update('contactEmail')}
                    testId="add-organization-email"
                />
            </div>
        </Modal>
    );
};

