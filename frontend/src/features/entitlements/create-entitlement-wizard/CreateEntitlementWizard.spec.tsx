import { act, screen } from "@testing-library/react";

import { renderWithQueryClient } from "~test-utils";

import {
  mockStepContext,
  mockUseSteps,
  mockUseUserRole,
  mockWizard,
} from "./CreateEntitlementWizard.spec.mocks";

import { CreateEntitlementWizard } from "./CreateEntitlementWizard";

function lastWizardProps() {
  return mockWizard.mock.lastCall![0];
}

describe("CreateEntitlementWizard", () => {
  beforeEach(() => {
    mockUseUserRole.mockReturnValue({ user: null, role: "operations" });
    mockUseSteps.mockReturnValue([{ title: "1" }, { title: "2" }, { title: "3" }, { title: "4" }]);
    mockStepContext.activeStepIndex = 0;
  });

  it("passes the initial saving state to useSteps", () => {
    renderWithQueryClient(<CreateEntitlementWizard isOpen onClose={jest.fn()} />);

    expect(mockUseSteps).toHaveBeenLastCalledWith(false);
  });

  it("passes the configured steps to the Wizard", () => {
    renderWithQueryClient(<CreateEntitlementWizard isOpen onClose={jest.fn()} />);

    expect(lastWizardProps().stepsProps).toHaveLength(4);
  });

  it("opens on the first step", () => {
    renderWithQueryClient(<CreateEntitlementWizard isOpen onClose={jest.fn()} />);

    expect(lastWizardProps().activeStepIndex).toBe(0);
  });

  it.each([
    ["affiliate", 0, "step-affiliate"],
    ["data source", 1, "step-datasource"],
    ["review", 2, "step-review"],
    ["summary", 3, "step-summary"],
  ] as const)("renders the %s step when it is active", (_name, index, testId) => {
    mockStepContext.activeStepIndex = index;

    renderWithQueryClient(<CreateEntitlementWizard isOpen onClose={jest.fn()} />);

    expect(screen.getByTestId(testId)).toBeInTheDocument();
  });

  it("closing the wizard reports an unsuccessful result when nothing was created", () => {
    const onClose = jest.fn();
    renderWithQueryClient(<CreateEntitlementWizard isOpen onClose={onClose} />);

    act(() => {
      lastWizardProps().onClose!();
    });

    expect(onClose).toHaveBeenCalledWith({ success: false });
  });

  it("saving the wizard reports an unsuccessful result when nothing was created", () => {
    const onClose = jest.fn();
    renderWithQueryClient(<CreateEntitlementWizard isOpen onClose={onClose} />);

    act(() => {
      lastWizardProps().onSave!();
    });

    expect(onClose).toHaveBeenCalledWith({ success: false });
  });
});
