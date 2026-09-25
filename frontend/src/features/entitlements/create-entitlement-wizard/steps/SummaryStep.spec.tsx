import type { ReactNode } from "react";

import { render, screen } from "@testing-library/react";
import { FormProvider, useForm } from "react-hook-form";

import type { AddWizardForm } from "../CreateEntitlement.Schema";
import { SummaryStep } from "./SummaryStep";

jest.mock("~shared/components/EntityProperties", () => ({
  EntityProps: () => <div data-testid="entity-props" />,
}));

jest.mock("~shared/components/wizard/WizardStep", () => ({
  WizardStep: ({
    title,
    error,
    children,
  }: {
    title: ReactNode;
    error?: string;
    children?: ReactNode;
  }) => (
    <div data-testid="wizard-step">
      <span data-testid="wizard-step-title">{title}</span>
      {error && <span data-testid="wizard-step-error">{error}</span>}
      {children}
    </div>
  ),
}));

jest.mock("@swo/design-system/notification", () => ({
  InlineNotification: ({ children }: { children?: ReactNode }) => (
    <div data-testid="success-notification">{children}</div>
  ),
}));

jest.mock("@swo/design-system/text", () => ({
  RegularText: ({ children }: { children?: ReactNode }) => <>{children}</>,
}));

function renderStep(error?: string, defaults?: Partial<AddWizardForm>) {
  function Wrapper() {
    const methods = useForm<AddWizardForm>({ defaultValues: defaults as AddWizardForm });
    return (
      <FormProvider {...methods}>
        <SummaryStep error={error} />
      </FormProvider>
    );
  }
  return render(<Wrapper />);
}

describe("SummaryStep", () => {
  it("shows the success notification when the entity has an id", () => {
    renderStep(undefined, { id: "new-id" });

    expect(screen.getByTestId("success-notification")).toBeInTheDocument();
  });

  it("does not show the success notification when the entity has no id", () => {
    renderStep(undefined, {});

    expect(screen.queryByTestId("success-notification")).not.toBeInTheDocument();
  });

  it("renders the error inside WizardStep when provided", () => {
    renderStep("failed", { id: "new-id" });

    expect(screen.getByTestId("wizard-step-error")).toHaveTextContent("failed");
  });
});
