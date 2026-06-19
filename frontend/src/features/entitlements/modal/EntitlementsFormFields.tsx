import { Control } from "react-hook-form";

import { InlineNotification } from "@swo/notification";

import { ControlledInput } from "~shared/components/form/ControlledInput";
import { useFixedT } from "~shared/hooks/useFixedT";

import { AddEntitlementForm } from "./AddEntitlementForm.Schema";

type Props = {
  control: Control<AddEntitlementForm>;
  error: string | null;
};

export const EntitlementsFormFields = ({ control, error }: Props) => {
  const tProperties = useFixedT("entitlement:properties");
  const tPlaceholders = useFixedT("entitlement:placeholders");
  const tEntitlement = useFixedT("entitlement");

  return (
    <div className="modal__content modal__container">
      {error && (
        <div className="modal__error">
          <InlineNotification status="error" isToShowCloseButton={false} width="auto">
            {error}
          </InlineNotification>
        </div>
      )}

      <p>{tEntitlement("create_info")}</p>
      <ControlledInput
        className="modal__input"
        control={control}
        name="name"
        type="default"
        label={tProperties("name")}
        labelType="required"
        placeholder={tPlaceholders("name")}
      />
      <ControlledInput
        className="modal__input"
        control={control}
        name="description"
        type="default"
        label={tProperties("description")}
        placeholder={tPlaceholders("description")}
      />
      <ControlledInput
        className="modal__input"
        control={control}
        name="contactEmail"
        type="default"
        label={tProperties("contactEmail")}
        placeholder={tPlaceholders("contactEmail")}
      />
    </div>
  );
};
