import type { ReactNode } from "react";

import { render, screen } from "@testing-library/react";
import type { Control } from "react-hook-form";

import { mockControlledInput, mockSharedControlledInput } from "~test-utils/mocks/controlledInput";

import type { EditOrganizationForm } from "./EditOrganization.Schema";
import { EditOrganizationFormFields } from "./EditOrganizationFormFields";

jest.mock("~shared/components/form/ControlledInput", () => mockSharedControlledInput);

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
