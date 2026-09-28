import { render } from "@testing-library/react";

import { makeEmployee, triggerModalCancel, triggerModalSubmit } from "~test-utils";
import { mockInlineErrorNotification, mockSharedInlineErrorNotification } from "~test-utils/mocks/inlineErrorNotification";
import { mockModal, mockSharedModal } from "~test-utils/mocks/modal";

import type { useEmployeeController } from "../hooks/useEmployeeController";
import { UserMakeAdminModal } from "./UserMakeAdminModal";

type Controller = ReturnType<typeof useEmployeeController>;

const mockUseEmployeeController = jest.fn() as jest.MockedFunction<typeof useEmployeeController>;

jest.mock("~shared/components/modal/Modal", () => mockSharedModal);
jest.mock("~shared/components/error/InlineErrorNotification", () => mockSharedInlineErrorNotification);

jest.mock("../hooks/useEmployeeController", () => ({
  useEmployeeController: (...args: Parameters<typeof useEmployeeController>) =>
    mockUseEmployeeController(...args),
}));

function primeController(overrides: Partial<Controller> = {}): Controller {
  const controller: Controller = {
    cancel: jest.fn(),
    makeAdmin: jest.fn().mockResolvedValue(undefined),
    isPending: false,
    error: null,
    ...overrides,
  };
  mockUseEmployeeController.mockReturnValue(controller);
  return controller;
}

describe("UserMakeAdminModal", () => {
  const employee = makeEmployee({ id: "emp-1" });

  beforeEach(() => {
    mockModal.mockClear();
    mockInlineErrorNotification.mockClear();
    mockUseEmployeeController.mockClear();
  });

  it("passes onClose to the employee controller", () => {
    primeController();
    const onClose = jest.fn();

    render(
      <UserMakeAdminModal isOpen onClose={onClose} employee={employee} organizationId="org-1" />,
    );

    expect(mockUseEmployeeController).toHaveBeenCalledWith({ onClose });
  });

  it("shows the controller error in the inline notification", () => {
    primeController({ error: "boom" });

    render(
      <UserMakeAdminModal isOpen onClose={jest.fn()} employee={employee} organizationId="org-1" />,
    );

    expect(mockInlineErrorNotification).toHaveBeenLastCalledWith({ error: "boom" });
  });

  it("makes the employee an admin and calls onSuccess after submit", async () => {
    const makeAdmin = jest.fn().mockResolvedValue(undefined);
    primeController({ makeAdmin });
    const onSuccess = jest.fn();

    render(
      <UserMakeAdminModal
        isOpen
        onClose={jest.fn()}
        employee={employee}
        organizationId="org-1"
        onSuccess={onSuccess}
      />,
    );
    await triggerModalSubmit(mockModal);

    expect(makeAdmin).toHaveBeenCalledWith({ organizationId: "org-1", employee });
    expect(onSuccess).toHaveBeenCalledTimes(1);
  });

  it("does not call makeAdmin when no employee is provided", async () => {
    const makeAdmin = jest.fn();
    primeController({ makeAdmin });

    render(
      <UserMakeAdminModal isOpen onClose={jest.fn()} employee={null} organizationId="org-1" />,
    );
    await triggerModalSubmit(mockModal);

    expect(makeAdmin).not.toHaveBeenCalled();
  });

  it("does not call makeAdmin when organizationId is missing", async () => {
    const makeAdmin = jest.fn();
    primeController({ makeAdmin });

    render(
      <UserMakeAdminModal isOpen onClose={jest.fn()} employee={employee} organizationId={null} />,
    );
    await triggerModalSubmit(mockModal);

    expect(makeAdmin).not.toHaveBeenCalled();
  });

  it("cancels through the employee controller when the modal is closed", () => {
    const controller = primeController();

    render(
      <UserMakeAdminModal isOpen onClose={jest.fn()} employee={employee} organizationId="org-1" />,
    );
    triggerModalCancel(mockModal);

    expect(controller.cancel).toHaveBeenCalledTimes(1);
  });
});
