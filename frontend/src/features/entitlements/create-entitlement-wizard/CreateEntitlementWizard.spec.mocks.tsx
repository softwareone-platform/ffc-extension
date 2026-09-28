import type { ComponentProps } from "react";

import type { useEntitlementsApi } from "~entitlements/api/useEntitlementsApi";
import { mockErrorDetailsModule } from "~test-utils/mocks/errorDetails";
import { mockUserRoleModule } from "~test-utils/mocks/userRole";

import type { ReviewStep } from "./steps/ReviewStep";
import type { SummaryStep } from "./steps/SummaryStep";

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

jest.mock("~entitlements/api/useEntitlementsApi", () => ({
  useEntitlementsApi: () => ({ save: mockSave }),
}));

jest.mock("~shared/hooks/useErrorDetails", () => mockErrorDetailsModule);
jest.mock("~shared/hooks/useUserRole", () => mockUserRoleModule);

jest.mock("@swo/design-system/modal", () => ({
  Modal: ({ children }: ModalProps) => <div data-testid="modal">{children}</div>,
}));

jest.mock("@swo/design-system/wizard", () => {
  const Wizard = (props: MockWizardProps) => {
    mockWizard(props);
    return <div data-testid="wizard">{props.children}</div>;
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
  useSteps: (...args: unknown[]) => mockUseSteps(...args),
}));
