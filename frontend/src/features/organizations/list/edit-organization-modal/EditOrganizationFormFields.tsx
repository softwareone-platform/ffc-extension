import { Control } from "react-hook-form";

import { InlineNotification } from "@swo/design-system/notification";

import { ControlledInput } from "~shared/components/form/ControlledInput";
import { useFixedT } from "~shared/hooks/useFixedT";

import { EditOrganizationForm } from "./EditOrganization.Schema";

type Props = {
  control: Control<EditOrganizationForm>;
  error: string | null;
};

export const EditOrganizationFormFields = ({ control, error }: Props) => {
  const tProperties = useFixedT("shared:properties");
  const tPlaceholders = useFixedT("shared:placeholders");

  return (
    <div className="modal__content modal__container">
      {error && (
        <div className="modal__error">
          <InlineNotification status="error" isToShowCloseButton={false} width="auto">
            {error}
          </InlineNotification>
        </div>
      )}
      <ControlledInput
        className="modal__input"
        control={control}
        name="name"
        type="default"
        isPreventAutocomplete={true}
        label={tProperties("name")}
        labelType="required"
        placeholder={tPlaceholders("name")}
      />
      <ControlledInput
        className="modal__input"
        control={control}
        name="operations_external_id"
        type="default"
        isPreventAutocomplete={true}
        label={tProperties("operations_external_id")}
        labelType="required"
        isDisabled={true}
        placeholder={tPlaceholders("operations_external_id")}
      />
      <ControlledInput
        className="modal__input"
        control={control}
        name="currency"
        type="default"
        isPreventAutocomplete={true}
        label={tProperties("currency")}
        labelType="required"
        isDisabled={true}
        placeholder={tPlaceholders("currency")}
      />
    </div>
  );
};
