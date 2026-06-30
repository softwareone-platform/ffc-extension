import { useCallback, useEffect, useMemo } from "react";

import { useFormContext, useFormState, useWatch } from "react-hook-form";

import { StepNavigationProperties, useStepActions } from "@swo/design-system/wizard";

import { Account } from "~features/entitlements/api/model";
import { SelectAffiliateList } from "~shared/components/SelectAffiliateList";
import { WizardStep } from "~shared/components/wizard/WizardStep";
import { useFixedT } from "~shared/hooks/useFixedT";

import { AddWizardForm } from "../CreateEntitlement.Schema";

export function AffiliateStep() {
  const tStep = useFixedT("entitlements:addWizard:steps:affiliate");

  const { trigger, setValue } = useFormContext<AddWizardForm>();
  const { registerOnNextCallback } = useStepActions();
  const [affiliate] = useWatch<Partial<AddWizardForm>, ["affiliate"]>({ name: ["affiliate"] });
  const formState = useFormState<AddWizardForm>({ name: "affiliate" });

  const onNext = useCallback(
    async ({ targetStepIndex, currentStepIndex }: StepNavigationProperties) => {
      const isValid = await trigger("affiliate", { shouldFocus: false });

      return isValid ? targetStepIndex : currentStepIndex;
    },
    [trigger],
  );

  useEffect(() => registerOnNextCallback(onNext), [onNext, registerOnNextCallback]);

  const errors = useMemo(() => {
    return formState.errors.affiliate?.message;
  }, [formState]);

  const onSelected = useCallback(
    (entity: Account) => {
      setValue("affiliate", entity as Required<Account>, {
        shouldValidate: true,
      });
    },
    [setValue],
  );

  return (
    <WizardStep title={tStep("title")} error={errors}>
      <SelectAffiliateList entity={affiliate as Account} onSelected={onSelected} />
    </WizardStep>
  );
}
