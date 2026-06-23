import { Control } from "react-hook-form";

import { InlineNotification } from "@swo/design-system/notification";

import { ControlledInput } from "~shared/components/form/ControlledInput";
import { useFixedT } from "~shared/hooks/useFixedT";

import { AddUserForm } from "./AddUserForm.Schema";

type Props = {
  control: Control<AddUserForm>;
  error: string | null;
};

export const UserFormFields = ({ control, error }: Props) => {
  const tProperties = useFixedT("shared:properties");
  const tPlaceholders = useFixedT("shared:placeholders");
  const tUsers = useFixedT("organization:users");

  return (
    <div className="modal__content modal__container">
      {error && (
        <div className="modal__error">
          <InlineNotification status="error" isToShowCloseButton={false} width="auto">
            {error}
          </InlineNotification>
        </div>
      )}

      <p>{tUsers("create_admin_info")}</p>
      <ControlledInput
        className="modal__input"
        control={control}
        name="email"
        type="default"
        isPreventAutocomplete={true}
        label={tProperties("email")}
        labelType="required"
        placeholder={tPlaceholders("email")}
      />
      <ControlledInput
        className="modal__input"
        control={control}
        name="display_name"
        type="default"
        isPreventAutocomplete={true}
        label={tProperties("display_name")}
        labelType="required"
        placeholder={tPlaceholders("display_name")}
      />
    </div>
  );
};
