import type { ComponentProps } from "react";

import { act, render } from "@testing-library/react";

import type { InlineErrorNotification } from "~shared/components/error/InlineErrorNotification";
import type { Modal } from "~shared/components/modal/Modal";
import { makeEmployee } from "~test-utils";

import type { useEmployeeController } from "../hooks/useEmployeeController";
import { UserMakeAdminModal } from "./UserMakeAdminModal";

type MockModalProps = ComponentProps<typeof Modal>;
type MockInlineErrorProps = ComponentProps<typeof InlineErrorNotification>;
type Controller = ReturnType<typeof useEmployeeController>;

const mockModal = jest.fn() as jest.MockedFunction<(props: MockModalProps) => void>;
const mockInlineErrorNotification = jest.fn() as jest.MockedFunction<
  (props: MockInlineErrorProps) => void
>;
const mockUseEmployeeController = jest.fn() as jest.MockedFunction<typeof useEmployeeController>;

jest.mock("~shared/components/modal/Modal", () => ({
  Modal: (props: MockModalProps) => {
    mockModal(props);
    return <div data-testid="modal">{props.children}</div>;
  },
}));

jest.mock("~shared/components/error/InlineErrorNotification", () => ({
  InlineErrorNotification: (props: MockInlineErrorProps) => {
    mockInlineErrorNotification(props);
    return <div data-testid="inline-error" />;
  },
}));

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

  it("passes onClose into the controller", () => {
    primeController();
    const onClose = jest.fn();

    render(
      <UserMakeAdminModal isOpen onClose={onClose} employee={employee} organizationId="org-1" />,
    );

    expect(mockUseEmployeeController).toHaveBeenCalledWith({ onClose });
  });

  it("forwards controller.error to InlineErrorNotification", () => {
    primeController({ error: "boom" });

    render(
      <UserMakeAdminModal isOpen onClose={jest.fn()} employee={employee} organizationId="org-1" />,
    );

    expect(mockInlineErrorNotification).toHaveBeenLastCalledWith({ error: "boom" });
  });

  it("submit invokes makeAdmin with organizationId and employee, then onSuccess", async () => {
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
    await act(async () => {
      await mockModal.mock.lastCall![0].onSubmit();
    });

    expect(makeAdmin).toHaveBeenCalledWith({ organizationId: "org-1", employee });
    expect(onSuccess).toHaveBeenCalledTimes(1);
  });

  it("submit is a noop when employee is null", () => {
    const makeAdmin = jest.fn();
    primeController({ makeAdmin });

    render(
      <UserMakeAdminModal isOpen onClose={jest.fn()} employee={null} organizationId="org-1" />,
    );
    act(() => {
      mockModal.mock.lastCall![0].onSubmit();
    });

    expect(makeAdmin).not.toHaveBeenCalled();
  });

  it("submit is a noop when organizationId is null", () => {
    const makeAdmin = jest.fn();
    primeController({ makeAdmin });

    render(
      <UserMakeAdminModal isOpen onClose={jest.fn()} employee={employee} organizationId={null} />,
    );
    act(() => {
      mockModal.mock.lastCall![0].onSubmit();
    });

    expect(makeAdmin).not.toHaveBeenCalled();
  });

  it("wires Modal onCancel to controller.cancel", () => {
    const controller = primeController();

    render(
      <UserMakeAdminModal isOpen onClose={jest.fn()} employee={employee} organizationId="org-1" />,
    );
    act(() => mockModal.mock.lastCall![0].onCancel?.());

    expect(controller.cancel).toHaveBeenCalledTimes(1);
  });
});
