import type { ComponentProps } from "react";

import { render } from "@testing-library/react";
import type { Control } from "react-hook-form";

import { makeOrganization, triggerModalCancel, triggerModalSubmit } from "~test-utils";
import { mockModal, mockSharedModal } from "~test-utils/mocks/modal";

import type { EditOrganizationForm } from "./EditOrganization.Schema";
import type { EditOrganizationFormFields } from "./EditOrganizationFormFields";
import { EditOrganizationModal } from "./EditOrganizationModal";
import type { useOrganizationsController } from "./hooks/useOrganizationsController";

type MockFormFieldsProps = ComponentProps<typeof EditOrganizationFormFields>;
type Controller = ReturnType<typeof useOrganizationsController>;

const mockFormFields = jest.fn() as jest.MockedFunction<(props: MockFormFieldsProps) => void>;
const mockUseOrganizationsController = jest.fn() as jest.MockedFunction<
  typeof useOrganizationsController
>;

jest.mock("~shared/components/modal/Modal", () => mockSharedModal);

jest.mock("./EditOrganizationFormFields", () => ({
  EditOrganizationFormFields: (props: MockFormFieldsProps) => {
    mockFormFields(props);
    return <div data-testid="form-fields" />;
  },
}));

jest.mock("./hooks/useOrganizationsController", () => ({
  useOrganizationsController: (...args: Parameters<typeof useOrganizationsController>) =>
    mockUseOrganizationsController(...args),
}));

function primeController(overrides: Partial<Controller> = {}): Controller {
  const controller: Controller = {
    handleCancel: jest.fn(),
    submit: jest.fn().mockResolvedValue(undefined),
    isPending: false,
    error: null,
    control: {} as Control<EditOrganizationForm>,
    ...overrides,
  };
  mockUseOrganizationsController.mockReturnValue(controller);
  return controller;
}

describe("EditOrganizationModal", () => {
  it("passes onClose and organization into the controller", () => {
    primeController();
    const onClose = jest.fn();
    const organization = makeOrganization();

    render(<EditOrganizationModal isOpen onClose={onClose} organization={organization} />);

    expect(mockUseOrganizationsController).toHaveBeenCalledWith({ onClose, organization });
  });

  it("forwards isSubmitting from controller.isPending", () => {
    primeController({ isPending: true });

    render(<EditOrganizationModal isOpen onClose={jest.fn()} organization={makeOrganization()} />);

    expect(mockModal.mock.lastCall![0]).toMatchObject({ isSubmitting: true });
  });

  it("wires Modal onCancel to controller.handleCancel", () => {
    const controller = primeController();

    render(<EditOrganizationModal isOpen onClose={jest.fn()} organization={makeOrganization()} />);
    triggerModalCancel(mockModal);

    expect(controller.handleCancel).toHaveBeenCalledTimes(1);
  });

  it("wires Modal onSubmit to controller.submit", async () => {
    const controller = primeController();

    render(<EditOrganizationModal isOpen onClose={jest.fn()} organization={makeOrganization()} />);
    await triggerModalSubmit(mockModal);

    expect(controller.submit).toHaveBeenCalledTimes(1);
  });

  it("passes controller.control and error to the form fields", () => {
    const control = {} as Control<EditOrganizationForm>;
    primeController({ control, error: "boom" });

    render(<EditOrganizationModal isOpen onClose={jest.fn()} organization={makeOrganization()} />);

    expect(mockFormFields).toHaveBeenLastCalledWith({ control, error: "boom" });
  });
});
