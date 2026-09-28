import { render } from "@testing-library/react";

import { makeEntitlement, triggerModalCancel, triggerModalSubmit } from "~test-utils";
import {
  mockInlineErrorNotification,
  mockSharedInlineErrorNotification,
} from "~test-utils/mocks/inlineErrorNotification";
import { mockModal, mockSharedModal } from "~test-utils/mocks/modal";

import type { useEntitlementController } from "../hooks/useEntitlementsController";
import { TerminateEntitlementModal } from "./TerminateEntitlementModal";

type Controller = ReturnType<typeof useEntitlementController>;

const mockUseEntitlementController = jest.fn() as jest.MockedFunction<
  typeof useEntitlementController
>;

jest.mock("~shared/components/modal/Modal", () => mockSharedModal);

jest.mock(
  "~shared/components/error/InlineErrorNotification",
  () => mockSharedInlineErrorNotification,
);

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

  it("passes onClose to the entitlement controller", () => {
    primeController();
    const onClose = jest.fn();

    render(<TerminateEntitlementModal isOpen onClose={onClose} entitlement={entitlement} />);

    expect(mockUseEntitlementController).toHaveBeenCalledWith({ onClose });
  });

  it("shows the controller error in the inline notification", () => {
    primeController({ error: "boom" });

    render(<TerminateEntitlementModal isOpen onClose={jest.fn()} entitlement={entitlement} />);

    expect(mockInlineErrorNotification).toHaveBeenLastCalledWith({ error: "boom" });
  });

  it("shows the submitting state while terminate is pending", () => {
    primeController({ isPendingTerminate: true });

    render(<TerminateEntitlementModal isOpen onClose={jest.fn()} entitlement={entitlement} />);

    expect(mockModal.mock.lastCall![0]).toMatchObject({ isSubmitting: true });
  });

  it("terminates the entitlement and calls onSuccess after submit", async () => {
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
    await triggerModalSubmit(mockModal);

    expect(terminate).toHaveBeenCalledWith(entitlement);
    expect(onSuccess).toHaveBeenCalledTimes(1);
  });

  it("does not call terminate when no entitlement is provided", async () => {
    const terminate = jest.fn();
    primeController({ terminate });

    render(<TerminateEntitlementModal isOpen onClose={jest.fn()} entitlement={null} />);
    await triggerModalSubmit(mockModal);

    expect(terminate).not.toHaveBeenCalled();
  });

  it("cancels through the entitlement controller when the modal is closed", () => {
    const controller = primeController();

    render(<TerminateEntitlementModal isOpen onClose={jest.fn()} entitlement={entitlement} />);
    triggerModalCancel(mockModal);

    expect(controller.cancel).toHaveBeenCalledTimes(1);
  });
});
