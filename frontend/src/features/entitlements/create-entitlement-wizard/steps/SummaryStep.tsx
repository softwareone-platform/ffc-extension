import { useFormContext } from "react-hook-form";

import { InlineNotification } from "@swo/design-system/notification";
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
  const entity = getValues();

  return (
    <WizardStep title={tStep("title")} error={error} className={"summary-step"}>
      {entity.id && (
        <div className="step__notification">
          <InlineNotification status="success" isToShowCloseButton={false} width="auto">
            <RegularText color="brand-type">{tStep("description")}</RegularText>
          </InlineNotification>
        </div>
      )}
      <EntityProps entity={entity} />
    </WizardStep>
  );
}
