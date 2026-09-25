import type { ComponentProps } from "react";

import { act, render } from "@testing-library/react";

import type { InlineErrorNotification } from "~shared/components/error/InlineErrorNotification";
import type { Modal } from "~shared/components/modal/Modal";
import { makeEntitlement } from "~test-utils";

import type { useEntitlementController } from "../hooks/useEntitlementsController";
import { TerminateEntitlementModal } from "./TerminateEntitlementModal";

type MockModalProps = ComponentProps<typeof Modal>;
type MockInlineErrorProps = ComponentProps<typeof InlineErrorNotification>;
type Controller = ReturnType<typeof useEntitlementController>;

const mockModal = jest.fn() as jest.MockedFunction<(props: MockModalProps) => void>;
const mockInlineErrorNotification = jest.fn() as jest.MockedFunction<
  (props: MockInlineErrorProps) => void
>;
const mockUseEntitlementController = jest.fn() as jest.MockedFunction<
  typeof useEntitlementController
>;

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

jest.mock("../hooks/useEntitlementsController", () => ({
  useEntitlementController: (...args: Parameters<typeof useEntitlementController>) =>
    mockUseEntitlementController(...args),
}));

function primeController(overrides: Partial<Controller> = {}): Controller {
  const controller: Controller = {
    cancel: jest.fn(),
    terminate: jest.fn().mockResolvedValue(undefined),
    remove: jest.fn().mockResolvedValue(undefined),
    error: null,
    isPendingTerminate: false,
    isPendingRemove: false,
    ...overrides,
  };
  mockUseEntitlementController.mockReturnValue(controller);
  return controller;
}

describe("TerminateEntitlementModal", () => {
  const entitlement = makeEntitlement({ id: "ent-1" });

  it("passes onClose into the controller", () => {
    primeController();
    const onClose = jest.fn();

    render(<TerminateEntitlementModal isOpen onClose={onClose} entitlement={entitlement} />);

    expect(mockUseEntitlementController).toHaveBeenCalledWith({ onClose });
  });

  it("forwards controller.error to InlineErrorNotification", () => {
    primeController({ error: "boom" });

    render(<TerminateEntitlementModal isOpen onClose={jest.fn()} entitlement={entitlement} />);

    expect(mockInlineErrorNotification).toHaveBeenLastCalledWith({ error: "boom" });
  });

  it("forwards isPendingTerminate to Modal isSubmitting", () => {
    primeController({ isPendingTerminate: true });

    render(<TerminateEntitlementModal isOpen onClose={jest.fn()} entitlement={entitlement} />);

    expect(mockModal.mock.lastCall![0]).toMatchObject({ isSubmitting: true });
  });

  it("submit invokes controller.terminate with the entitlement then onSuccess", async () => {
    const terminate = jest.fn().mockResolvedValue(undefined);
    primeController({ terminate });
    const onSuccess = jest.fn();

    render(
      <TerminateEntitlementModal
        isOpen
        onClose={jest.fn()}
        entitlement={entitlement}
        onSuccess={onSuccess}
      />,
    );
    await act(async () => {
      await mockModal.mock.lastCall![0].onSubmit();
    });

    expect(terminate).toHaveBeenCalledWith(entitlement);
    expect(onSuccess).toHaveBeenCalledTimes(1);
  });

  it("submit is a noop when entitlement is null", () => {
    const terminate = jest.fn();
    primeController({ terminate });

    render(<TerminateEntitlementModal isOpen onClose={jest.fn()} entitlement={null} />);
    act(() => {
      mockModal.mock.lastCall![0].onSubmit();
    });

    expect(terminate).not.toHaveBeenCalled();
  });

  it("wires Modal onCancel to controller.cancel", () => {
    const controller = primeController();

    render(<TerminateEntitlementModal isOpen onClose={jest.fn()} entitlement={entitlement} />);
    act(() => mockModal.mock.lastCall![0].onCancel?.());

    expect(controller.cancel).toHaveBeenCalledTimes(1);
  });
});
