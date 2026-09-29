import type { ComponentProps } from "react";

import type { WizardStep } from "~shared/components/wizard/WizardStep";

type MockWizardStepProps = Pick<ComponentProps<typeof WizardStep>, "title" | "error" | "children">;

export const mockSharedWizardStep = {
  WizardStep: ({ title, error, children }: MockWizardStepProps) => (
    <div data-testid="wizard-step">
      {title !== undefined && <span data-testid="wizard-step-title">{title}</span>}
      {error && <span data-testid="wizard-step-error">{error}</span>}
      {children}
    </div>
  ),
};
