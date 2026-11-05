import type { ComponentProps } from "react";

import type { useEntitlementsApi } from "~entitlements/api/useEntitlementsApi";
import { mockErrorDetailsModule } from "~test-utils/mocks/errorDetails";
import { mockUserRoleModule } from "~test-utils/mocks/userRole";

import type { AddWizardForm } from "./CreateEntitlement.Schema";
import type { ReviewStep } from "./steps/ReviewStep";
import type { SummaryStep } from "./steps/SummaryStep";
import type { useSteps } from "./useSteps";

export { mockGetErrorMessage } from "~test-utils/mocks/errorDetails";
export { mockUseUserRole } from "~test-utils/mocks/userRole";

type EntitlementsApi = ReturnType<typeof useEntitlementsApi>;
type MockWizardProps = ComponentProps<typeof import("@swo/design-system/wizard").Wizard>;
type ModalProps = ComponentProps<typeof import("@swo/design-system/modal").Modal>;
type WizardHeaderProps = ComponentProps<typeof import("@swo/design-system/wizard").Wizard.Header>;
type WizardContentProps = ComponentProps<typeof import("@swo/design-system/wizard").Wizard.Content>;
type WizardStepContentProps = ComponentProps<
  typeof import("@swo/design-system/wizard").Wizard.Content.StepContent
>;
type ReviewStepProps = ComponentProps<typeof ReviewStep>;
type SummaryStepProps = ComponentProps<typeof SummaryStep>;

export const mockSave = jest.fn() as jest.MockedFunction<EntitlementsApi["save"]>;
export const mockWizard = jest.fn() as jest.MockedFunction<(props: MockWizardProps) => void>;
export const mockUseSteps = jest.fn();

// Mutable object so the Wizard.Content.StepContent mock reads the current index
// per render. Tests mutate `.activeStepIndex` before rendering.
export const mockStepContext = { activeStepIndex: 0 };

// Schema-valid values written into the real form by the "fill form" button,
// so `handleSubmit` passes zod validation and reaches the mutation.
export const mockValidForm: AddWizardForm = {
  name: "My entitlement",
  affiliate: { id: "acc-1", name: "Affiliate 1", integration: "aws", cloud_provider: null },
  dataSource: { id: "ds-1", affiliate_external_id: "ext-1" },
};

jest.mock("~entitlements/api/useEntitlementsApi", () => ({
  useEntitlementsApi: () => ({ save: mockSave }),
}));

jest.mock("~shared/hooks/useErrorDetails", () => mockErrorDetailsModule);
jest.mock("~shared/hooks/useUserRole", () => mockUserRoleModule);

jest.mock("@swo/design-system/modal", () => ({
  Modal: ({ children, onClose }: ModalProps) => (
    <div data-testid="modal">
      <button onClick={() => onClose?.()} type="button">
        dismiss modal
      </button>
      {children}
    </div>
  ),
}));

jest.mock("@swo/design-system/wizard", () => {
  const { useFormContext } =
    jest.requireActual<typeof import("react-hook-form")>("react-hook-form");

  // Stands in for the (mocked) steps editing the real form owned by the wizard.
  const FormControls = () => {
    const { setValue } = useFormContext<AddWizardForm>();
    const fillForm = () => {
      setValue("name", mockValidForm.name);
      setValue("affiliate", mockValidForm.affiliate);
      setValue("dataSource", mockValidForm.dataSource);
    };

    return (
      <>
        <button onClick={fillForm} type="button">
          fill form
        </button>
        <button onClick={() => setValue("name", "Edited", { shouldDirty: true })} type="button">
          change name
        </button>
        <button onClick={() => setValue("name", "Edited")} type="button">
          change name without dirtying
        </button>
      </>
    );
  };

  const Wizard = (props: MockWizardProps) => {
    mockWizard(props);
    return (
      <form data-testid="wizard" onSubmit={props.onSubmit}>
        <button onClick={() => props.onClose?.()} type="button">
          close wizard
        </button>
        <button onClick={() => props.onSave?.()} type="button">
          save wizard
        </button>
        <button type="submit">submit wizard</button>
        <FormControls />
        {props.children}
      </form>
    );
  };
  Wizard.Header = ({ children }: WizardHeaderProps) => (
    <div data-testid="wizard-header">{children}</div>
  );
  const Content = ({ children }: WizardContentProps) => (
    <div data-testid="wizard-content">{children}</div>
  );
  Content.Steps = () => <div data-testid="wizard-steps" />;
  Content.StepContent = ({ children }: WizardStepContentProps) => {
    return (
      <div data-testid="wizard-step-content">
        {typeof children === "function"
          ? children({
              activeStepIndex: mockStepContext.activeStepIndex,
              goToNext: jest.fn(),
              goBack: jest.fn(),
              goTo: jest.fn(),
              close: jest.fn(),
            })
          : children}
      </div>
    );
  };
  Wizard.Content = Content;
  Wizard.Actions = () => <div data-testid="wizard-actions" />;
  return { Wizard };
});

jest.mock("./steps/AffiliateStep", () => ({
  AffiliateStep: () => <div data-testid="step-affiliate" />,
}));

jest.mock("./steps/DataSourceStep", () => ({
  DataSourceStep: () => <div data-testid="step-datasource" />,
}));

jest.mock("./steps/ReviewStep", () => ({
  ReviewStep: ({ error }: ReviewStepProps) => <div data-testid="step-review" data-error={error} />,
}));

jest.mock("./steps/SummaryStep", () => ({
  SummaryStep: ({ error }: SummaryStepProps) => (
    <div data-testid="step-summary" data-error={error} />
  ),
}));

jest.mock("./useSteps", () => ({
  useSteps: (...args: Parameters<typeof useSteps>) => mockUseSteps(...args),
}));
