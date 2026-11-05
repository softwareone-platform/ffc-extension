import type { ReactNode } from "react";

import { render } from "@testing-library/react";
import { FormProvider, useForm } from "react-hook-form";

import type { AddWizardForm } from "../CreateEntitlement.Schema";

export type WizardStepRenderOptions = {
  defaultValues?: Partial<AddWizardForm>;
  triggerResolvedValue?: boolean;
  /** Field names reported as dirty by `getFieldState`. */
  dirtyFields?: string[];
};

export type WizardStepRenderResult = {
  setValue: jest.Mock;
  trigger: jest.Mock;
};

export function renderWizardStep(
  element: ReactNode,
  { defaultValues, triggerResolvedValue = true, dirtyFields = [] }: WizardStepRenderOptions = {},
): WizardStepRenderResult {
  const trigger = jest.fn().mockResolvedValue(triggerResolvedValue);
  const setValue = jest.fn();

  function Wrapper() {
    const methods = useForm<AddWizardForm>({ defaultValues: defaultValues as AddWizardForm });
    const { getFieldState } = methods;
    methods.trigger = trigger as unknown as typeof methods.trigger;
    methods.setValue = setValue as unknown as typeof methods.setValue;
    methods.getFieldState = ((name, formState) => ({
      ...getFieldState(name, formState),
      isDirty: dirtyFields.includes(name),
    })) as typeof methods.getFieldState;

    return <FormProvider {...methods}>{element}</FormProvider>;
  }

  render(<Wrapper />);

  return { setValue, trigger };
}
