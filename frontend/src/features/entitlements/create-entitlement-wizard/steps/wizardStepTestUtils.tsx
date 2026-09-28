import type { ReactNode } from "react";

import { render } from "@testing-library/react";
import { FormProvider, useForm } from "react-hook-form";

import type { AddWizardForm } from "../CreateEntitlement.Schema";

export type WizardStepRenderOptions = {
  defaultValues?: Partial<AddWizardForm>;
  triggerResolvedValue?: boolean;
};

export type WizardStepRenderResult = {
  setValue: jest.Mock;
  trigger: jest.Mock;
};

export function renderWizardStep(
  element: ReactNode,
  { defaultValues, triggerResolvedValue = true }: WizardStepRenderOptions = {},
): WizardStepRenderResult {
  const trigger = jest.fn().mockResolvedValue(triggerResolvedValue);
  const setValue = jest.fn();

  function Wrapper() {
    const methods = useForm<AddWizardForm>({ defaultValues: defaultValues as AddWizardForm });
    methods.trigger = trigger as unknown as typeof methods.trigger;
    methods.setValue = setValue as unknown as typeof methods.setValue;

    return <FormProvider {...methods}>{element}</FormProvider>;
  }

  render(<Wrapper />);

  return { setValue, trigger };
}

