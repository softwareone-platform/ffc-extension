import { useFormContext } from "react-hook-form";

import { RegularText } from "@swo/design-system/text";

import { EntityProps } from "~shared/components/EntityProperties";
import { WizardStep } from "~shared/components/wizard/WizardStep";
import { useFixedT } from "~shared/hooks/useFixedT";

import { AddWizardForm } from "../CreateEntitlement.Schema";

export interface SummaryStepProps {
  readonly error?: string;
}

export function SummaryStep({ error }: SummaryStepProps) {
  const tStep = useFixedT("entitlements:addWizard:steps:summary");
  const { getValues } = useFormContext<AddWizardForm>();

  return (
    <WizardStep title={tStep("title")} error={error} className={"summary-step"}>
      <RegularText color="brand-type">{tStep("description")}</RegularText>
      <EntityProps entity={getValues()} />
    </WizardStep>
  );
}
