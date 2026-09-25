import type { ComponentProps } from "react";

import { act, render } from "@testing-library/react";
import type { Control } from "react-hook-form";

import type { Modal } from "~shared/components/modal/Modal";

import type { AddUserForm } from "./AddUserForm.Schema";
import { CreateUserModal } from "./CreateUserModal";
import type { useUserFormController } from "./hooks/useUserFormController";
import type { UserFormFields } from "./UserFormFields";

type MockModalProps = ComponentProps<typeof Modal>;
type MockFormFieldsProps = ComponentProps<typeof UserFormFields>;
type Controller = ReturnType<typeof useUserFormController>;

const mockModal = jest.fn() as jest.MockedFunction<(props: MockModalProps) => void>;
const mockFormFields = jest.fn() as jest.MockedFunction<(props: MockFormFieldsProps) => void>;
const mockUseUserFormController = jest.fn() as jest.MockedFunction<typeof useUserFormController>;

jest.mock("~shared/components/modal/Modal", () => ({
  Modal: (props: MockModalProps) => {
    mockModal(props);
    return <div data-testid="modal">{props.children}</div>;
  },
}));

jest.mock("./UserFormFields", () => ({
  UserFormFields: (props: MockFormFieldsProps) => {
    mockFormFields(props);
    return <div data-testid="form-fields" />;
  },
}));

jest.mock("./hooks/useUserFormController", () => ({
  useUserFormController: (...args: Parameters<typeof useUserFormController>) =>
    mockUseUserFormController(...args),
}));

function primeController(overrides: Partial<Controller> = {}): Controller {
  const controller: Controller = {
    control: {} as Control<AddUserForm>,
    error: null,
    isPending: false,
    submit: jest.fn().mockResolvedValue(undefined),
    handleCancel: jest.fn(),
    ...overrides,
  };
  mockUseUserFormController.mockReturnValue(controller);
  return controller;
}

describe("CreateUserModal", () => {
  it("passes onClose and organizationId into the controller", () => {
    primeController();
    const onClose = jest.fn();

    render(<CreateUserModal isOpen onClose={onClose} organizationId="org-1" />);

    expect(mockUseUserFormController).toHaveBeenCalledWith({ onClose, organizationId: "org-1" });
  });

  it("forwards isSubmitting from controller.isPending", () => {
    primeController({ isPending: true });

    render(<CreateUserModal isOpen onClose={jest.fn()} organizationId="org-1" />);

    expect(mockModal.mock.lastCall![0]).toMatchObject({ isSubmitting: true });
  });

  it("wires Modal onCancel to controller.handleCancel", () => {
    const controller = primeController();

    render(<CreateUserModal isOpen onClose={jest.fn()} organizationId="org-1" />);
    act(() => mockModal.mock.lastCall![0].onCancel?.());

    expect(controller.handleCancel).toHaveBeenCalledTimes(1);
  });

  it("wires Modal onSubmit to controller.submit", () => {
    const controller = primeController();

    render(<CreateUserModal isOpen onClose={jest.fn()} organizationId="org-1" />);
    act(() => {
      mockModal.mock.lastCall![0].onSubmit();
    });

    expect(controller.submit).toHaveBeenCalledTimes(1);
  });

  it("passes controller.control and error to the form fields", () => {
    const control = {} as Control<AddUserForm>;
    primeController({ control, error: "boom" });

    render(<CreateUserModal isOpen onClose={jest.fn()} organizationId="org-1" />);

    expect(mockFormFields).toHaveBeenLastCalledWith({ control, error: "boom" });
  });
});
