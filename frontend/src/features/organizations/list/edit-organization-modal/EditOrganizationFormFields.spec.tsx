import type { ComponentProps, ReactNode } from "react";

import { render, screen } from "@testing-library/react";
import type { Control } from "react-hook-form";

import type { ControlledInput } from "~shared/components/form/ControlledInput";

import type { EditOrganizationForm } from "./EditOrganization.Schema";
import { EditOrganizationFormFields } from "./EditOrganizationFormFields";

type MockControlledInputProps = ComponentProps<typeof ControlledInput>;

const mockControlledInput = jest.fn() as jest.MockedFunction<
  (props: MockControlledInputProps) => void
>;

jest.mock("~shared/components/form/ControlledInput", () => ({
  ControlledInput: (props: MockControlledInputProps) => {
    mockControlledInput(props);
    return <input data-testid={`input-${props.name}`} disabled={props.isDisabled} />;
  },
}));

jest.mock("@swo/design-system/notification", () => ({
  InlineNotification: ({ children }: { children?: ReactNode }) => (
    <div data-testid="inline-notification">{children}</div>
  ),
}));

function renderFields(error: string | null = null) {
  return render(
    <EditOrganizationFormFields control={{} as Control<EditOrganizationForm>} error={error} />,
  );
}

describe("EditOrganizationFormFields", () => {
  it("renders three ControlledInputs — name, operations_external_id, and currency", () => {
    renderFields();

    const names = mockControlledInput.mock.calls.map(([props]) => props.name);
    expect(names).toEqual(["name", "operations_external_id", "currency"]);
  });

  it("disables operations_external_id and currency but keeps name editable", () => {
    renderFields();

    expect(screen.getByTestId("input-name")).toBeEnabled();
    expect(screen.getByTestId("input-operations_external_id")).toBeDisabled();
    expect(screen.getByTestId("input-currency")).toBeDisabled();
  });

  it("does not render an inline notification when error is null", () => {
    renderFields(null);

    expect(screen.queryByTestId("inline-notification")).not.toBeInTheDocument();
  });

  it("renders the error message in an inline notification when error is set", () => {
    renderFields("something broke");

    expect(screen.getByTestId("inline-notification")).toHaveTextContent("something broke");
  });
});
