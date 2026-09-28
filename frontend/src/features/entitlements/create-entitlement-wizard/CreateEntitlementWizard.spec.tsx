import type { ReactNode } from "react";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { act, render, screen } from "@testing-library/react";

import {
  mockStepContext,
  mockUseSteps,
  mockUseUserRole,
  mockWizard,
} from "./CreateEntitlementWizard.spec.mocks";

import { CreateEntitlementWizard } from "./CreateEntitlementWizard";

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
    mockStepContext.activeStepIndex = 0;
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
    mockStepContext.activeStepIndex = index;

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
