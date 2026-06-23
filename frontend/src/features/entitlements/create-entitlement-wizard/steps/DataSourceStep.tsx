import { useCallback, useEffect } from "react";

import { useFormContext, useFormState } from "react-hook-form";

import { RegularText } from "@swo/design-system/text";
import { StepNavigationProperties, useStepActions } from "@swo/design-system/wizard";

import { ControlledInput } from "~shared/components/form/ControlledInput";
import { WizardStep } from "~shared/components/wizard/WizardStep";
import { useFixedT } from "~shared/hooks/useFixedT";

import { AddWizardForm } from "../CreateEntitlement.Schema";

export function DataSourceStep() {
  const tStep = useFixedT("entitlements:addWizard:steps:dataSource");
  const tProperties = useFixedT("entitlements:addWizard:properties:dataSource");
  const tPlaceholders = useFixedT("entitlements:addWizard:placeholders:dataSource");

  const { trigger, control, setValue } = useFormContext<AddWizardForm>();

  const { registerOnNextCallback } = useStepActions();
  const formState = useFormState<AddWizardForm>({ name: "dataSource" });

  const onNext = useCallback(
    async ({ targetStepIndex, currentStepIndex }: StepNavigationProperties) => {
      const isValid = await trigger(["name", "dataSource"], { shouldFocus: false });
      return isValid ? targetStepIndex : currentStepIndex;
    },
    [trigger],
  );

  useEffect(() => registerOnNextCallback(onNext), [onNext, registerOnNextCallback]);

  return (
    <WizardStep title={tStep("title")}>
      <div className={"step-input"}>
        <ControlledInput
          control={control}
          name="name"
          isPreventAutocomplete={true}
          label={tProperties("name")}
          placeholder={tPlaceholders("name")}
        />
      </div>
      <div className={"step-input"}>
        <ControlledInput
          control={control}
          name="dataSource.id"
          isPreventAutocomplete={true}
          label={tProperties("id")}
          placeholder={tPlaceholders("id")}
        />
        <RegularText size={1}>{tStep("field:id:description")}</RegularText>
      </div>
      <div className={"step-input"}>
        <ControlledInput
          control={control}
          name="dataSource.affiliate_external_id"
          isPreventAutocomplete={true}
          label={tProperties("affiliateExternalId")}
          placeholder={tPlaceholders("affiliateExternalId")}
          labelType="optional"
        />
        <RegularText size={1}>{tStep("field:affiliate_external_id:description")}</RegularText>
      </div>
    </WizardStep>
  );
}
