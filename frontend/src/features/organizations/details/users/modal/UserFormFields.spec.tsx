import { render, screen } from "@testing-library/react";
import type { Control } from "react-hook-form";

import { mockControlledInput, mockSharedControlledInput } from "~test-utils/mocks/controlledInput";
import { mockDesignSystemNotification } from "~test-utils/mocks/designSystemNotification";

import type { AddUserForm } from "./AddUserForm.Schema";
import { UserFormFields } from "./UserFormFields";

jest.mock("~shared/components/form/ControlledInput", () => mockSharedControlledInput);
jest.mock("@swo/design-system/notification", () => mockDesignSystemNotification);

function renderFields(error: string | null = null) {
  return render(<UserFormFields control={{} as Control<AddUserForm>} error={error} />);
}

describe("UserFormFields", () => {
  it("renders two ControlledInputs — email and display_name", () => {
    renderFields();

    const names = mockControlledInput.mock.calls.map(([props]) => props.name);
    expect(names).toEqual(["email", "display_name"]);
  });

  it("does not render an inline notification when error is null", () => {
    renderFields(null);

    expect(screen.queryByTestId("inline-notification")).not.toBeInTheDocument();
  });

  it("renders the error message in an inline notification when error is set", () => {
    renderFields("bad email");

    expect(screen.getByTestId("inline-notification")).toHaveTextContent("bad email");
  });
});
