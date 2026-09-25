import type { ReactNode } from "react";

import { render } from "@testing-library/react";
import { FormProvider, useForm } from "react-hook-form";

import type { StepNavigationProperties } from "@swo/design-system/wizard";

import { mockControlledInput, mockSharedControlledInput } from "~test-utils/mocks/controlledInput";

import type { AddWizardForm } from "../CreateEntitlement.Schema";
import { DataSourceStep } from "./DataSourceStep";

const mockRegisterOnNextCallback = jest.fn();

jest.mock("@swo/design-system/wizard", () => ({
  useStepActions: () => ({ registerOnNextCallback: mockRegisterOnNextCallback }),
}));

jest.mock("~shared/components/form/ControlledInput", () => mockSharedControlledInput);

jest.mock("~shared/components/wizard/WizardStep", () => ({
  WizardStep: ({ children }: { children?: ReactNode }) => (
    <div data-testid="wizard-step">{children}</div>
  ),
}));

jest.mock("@swo/design-system/text", () => ({
  RegularText: ({ children }: { children?: ReactNode }) => <>{children}</>,
}));

function renderStep() {
  const triggerSpy = jest.fn().mockResolvedValue(true);
  function Wrapper() {
    const methods = useForm<AddWizardForm>();
    methods.trigger = triggerSpy as unknown as typeof methods.trigger;
    return (
      <FormProvider {...methods}>
        <DataSourceStep />
      </FormProvider>
    );
  }
  render(<Wrapper />);
  return { triggerSpy };
}

describe("DataSourceStep", () => {
  it("renders the name, dataSource.id, and dataSource.affiliate_external_id inputs", () => {
    renderStep();

    const names = Array.from(new Set(mockControlledInput.mock.calls.map(([props]) => props.name)));
    expect(names).toEqual(["name", "dataSource.id", "dataSource.affiliate_external_id"]);
  });

  it("registers an onNext callback that validates name and dataSource fields", async () => {
    const { triggerSpy } = renderStep();

    const onNext = mockRegisterOnNextCallback.mock.lastCall![0] as (
      props: StepNavigationProperties,
    ) => Promise<number>;

    const nextIndex = await onNext({
      targetStepIndex: 2,
      currentStepIndex: 1,
    } as StepNavigationProperties);

    expect(triggerSpy).toHaveBeenCalledWith(["name", "dataSource"], { shouldFocus: false });
    expect(nextIndex).toBe(2);
  });

  it("keeps the current step when validation fails", async () => {
    const triggerSpy = jest.fn().mockResolvedValue(false);
    function Wrapper() {
      const methods = useForm<AddWizardForm>();
      methods.trigger = triggerSpy as unknown as typeof methods.trigger;
      return (
        <FormProvider {...methods}>
          <DataSourceStep />
        </FormProvider>
      );
    }
    render(<Wrapper />);

    const onNext = mockRegisterOnNextCallback.mock.lastCall![0] as (
      props: StepNavigationProperties,
    ) => Promise<number>;
    const nextIndex = await onNext({
      targetStepIndex: 2,
      currentStepIndex: 1,
    } as StepNavigationProperties);

    expect(nextIndex).toBe(1);
  });
});
