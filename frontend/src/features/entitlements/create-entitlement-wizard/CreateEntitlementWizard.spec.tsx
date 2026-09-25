import type { ComponentProps, ReactNode } from "react";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, render, screen } from "@testing-library/react";

import type { useEntitlementsApi } from "~entitlements/api/useEntitlementsApi";
import type { useErrorDetails } from "~shared/hooks/useErrorDetails";
import type { useUserRole } from "~shared/hooks/useUserRole";

import { CreateEntitlementWizard } from "./CreateEntitlementWizard";

type EntitlementsApi = ReturnType<typeof useEntitlementsApi>;
type ErrorDetails = ReturnType<typeof useErrorDetails>;
type MockWizardProps = ComponentProps<typeof import("@swo/design-system/wizard").Wizard>;

const mockSave = jest.fn() as jest.MockedFunction<EntitlementsApi["save"]>;
const mockGetErrorMessage = jest.fn() as jest.MockedFunction<ErrorDetails["getErrorMessage"]>;
const mockUseUserRole = jest.fn() as jest.MockedFunction<typeof useUserRole>;
const mockWizard = jest.fn() as jest.MockedFunction<(props: MockWizardProps) => void>;
const mockUseSteps = jest.fn();

let stepContentActiveIndex = 0;

jest.mock("~entitlements/api/useEntitlementsApi", () => ({
  useEntitlementsApi: () => ({ save: mockSave }),
}));

jest.mock("~shared/hooks/useErrorDetails", () => ({
  useErrorDetails: () => ({ getErrorMessage: mockGetErrorMessage }),
}));

jest.mock("~shared/hooks/useUserRole", () => ({
  useUserRole: () => mockUseUserRole(),
}));

jest.mock("@swo/design-system/modal", () => ({
  Modal: ({ children }: { children?: ReactNode }) => <div data-testid="modal">{children}</div>,
}));

jest.mock("@swo/design-system/wizard", () => {
  const Wizard = (props: MockWizardProps) => {
    mockWizard(props);
    return <div data-testid="wizard">{props.children}</div>;
  };
  Wizard.Header = ({ children }: { children?: ReactNode }) => (
    <div data-testid="wizard-header">{children}</div>
  );
  const Content = ({ children }: { children?: ReactNode }) => (
    <div data-testid="wizard-content">{children}</div>
  );
  Content.Steps = () => <div data-testid="wizard-steps" />;
  Content.StepContent = ({
    children,
  }: {
    children: (ctx: { activeStepIndex: number }) => ReactNode;
  }) => (
    <div data-testid="wizard-step-content">
      {children({ activeStepIndex: stepContentActiveIndex })}
    </div>
  );
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
  ReviewStep: ({ error }: { error?: string }) => (
    <div data-testid="step-review" data-error={error} />
  ),
}));

jest.mock("./steps/SummaryStep", () => ({
  SummaryStep: ({ error }: { error?: string }) => (
    <div data-testid="step-summary" data-error={error} />
  ),
}));

jest.mock("./useSteps", () => ({
  useSteps: (...args: unknown[]) => mockUseSteps(...args),
}));

function withQueryClient(ui: ReactNode) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return <QueryClientProvider client={client}>{ui}</QueryClientProvider>;
}

function primeOperations() {
  mockUseUserRole.mockReturnValue({ user: null, role: "operations" });
}

function lastWizardProps() {
  return mockWizard.mock.lastCall![0];
}

describe("CreateEntitlementWizard", () => {
  beforeEach(() => {
    primeOperations();
    mockUseSteps.mockReturnValue([{ title: "1" }, { title: "2" }, { title: "3" }, { title: "4" }]);
    stepContentActiveIndex = 0;
  });

  it("initialises useSteps with isPending=false", () => {
    render(withQueryClient(<CreateEntitlementWizard isOpen onClose={jest.fn()} />));

    expect(mockUseSteps).toHaveBeenLastCalledWith(false);
  });

  it("passes the useSteps result to the Wizard as stepsProps", () => {
    render(withQueryClient(<CreateEntitlementWizard isOpen onClose={jest.fn()} />));

    expect(lastWizardProps().stepsProps).toHaveLength(4);
  });

  it("starts at activeStepIndex=0", () => {
    render(withQueryClient(<CreateEntitlementWizard isOpen onClose={jest.fn()} />));

    expect(lastWizardProps().activeStepIndex).toBe(0);
  });

  it.each([
    ["affiliate", 0, "step-affiliate"],
    ["dataSource", 1, "step-datasource"],
    ["review", 2, "step-review"],
    ["summary", 3, "step-summary"],
  ] as const)("renders %s step at activeStepIndex=%i", (_name, index, testId) => {
    stepContentActiveIndex = index;

    render(withQueryClient(<CreateEntitlementWizard isOpen onClose={jest.fn()} />));

    expect(screen.getByTestId(testId)).toBeInTheDocument();
  });

  it("Wizard onClose reports success=false when no entitlement was created", () => {
    const onClose = jest.fn();
    render(withQueryClient(<CreateEntitlementWizard isOpen onClose={onClose} />));

    act(() => {
      lastWizardProps().onClose!();
    });

    expect(onClose).toHaveBeenCalledWith({ success: false });
  });

  it("Wizard onSave reports success=false when no entitlement was created", () => {
    const onClose = jest.fn();
    render(withQueryClient(<CreateEntitlementWizard isOpen onClose={onClose} />));

    act(() => {
      lastWizardProps().onSave!();
    });

    expect(onClose).toHaveBeenCalledWith({ success: false });
  });
});
