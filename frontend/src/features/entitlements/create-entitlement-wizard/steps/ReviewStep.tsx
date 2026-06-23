import { useFormContext } from "react-hook-form";

import { RegularText } from "@swo/design-system/text";

import { EntityProps } from "~shared/components/EntityProperties";
import { WizardStep } from "~shared/components/wizard/WizardStep";
import { useFixedT } from "~shared/hooks/useFixedT";

import { AddWizardForm } from "../CreateEntitlement.Schema";

export interface ReviewStepProps {
  error?: string;
}

export function ReviewStep({ error }: ReviewStepProps) {
  const tStep = useFixedT("entitlements:addWizard:steps:overview");
  const { getValues } = useFormContext<AddWizardForm>();

  return (
    <WizardStep title={tStep("title")} error={error} className={"review-step"}>
      <RegularText color="brand-type">{tStep("description")}</RegularText>
      <EntityProps entity={getValues()} />
    </WizardStep>
  );
}
