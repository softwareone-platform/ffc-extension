import { render, screen } from "@testing-library/react";
import { FormProvider, useForm } from "react-hook-form";

import { mockDesignSystemText } from "~test-utils/mocks/designSystemText";
import { mockSharedWizardStep } from "~test-utils/mocks/wizardStep";

import type { AddWizardForm } from "../CreateEntitlement.Schema";
import { ReviewStep } from "./ReviewStep";

const mockEntityProps = jest.fn() as jest.MockedFunction<
  (props: { entity: Partial<AddWizardForm> }) => void
>;

jest.mock("~shared/components/EntityProperties", () => ({
  EntityProps: (props: { entity: Partial<AddWizardForm> }) => {
    mockEntityProps(props);
    return <div data-testid="entity-props" />;
  },
}));

jest.mock("~shared/components/wizard/WizardStep", () => mockSharedWizardStep);

jest.mock("@swo/design-system/text", () => mockDesignSystemText);

function renderStep(error?: string, defaults?: Partial<AddWizardForm>) {
  function Wrapper() {
    const methods = useForm<AddWizardForm>({ defaultValues: defaults as AddWizardForm });
    return (
      <FormProvider {...methods}>
        <ReviewStep error={error} />
      </FormProvider>
    );
  }
  return render(<Wrapper />);
}

describe("ReviewStep", () => {
  it("passes the current form values to EntityProps", () => {
    const values = {
      name: "My entitlement",
      dataSource: { id: "ds", affiliate_external_id: "ext" },
    } as unknown as Partial<AddWizardForm>;

    renderStep(undefined, values);

    expect(mockEntityProps).toHaveBeenCalledWith({
      entity: expect.objectContaining(values),
    });
  });

  it("does not render an error when none is passed", () => {
    renderStep();

    expect(screen.queryByTestId("wizard-step-error")).not.toBeInTheDocument();
  });

  it("renders the error inside WizardStep when provided", () => {
    renderStep("something failed");

    expect(screen.getByTestId("wizard-step-error")).toHaveTextContent("something failed");
  });
});
