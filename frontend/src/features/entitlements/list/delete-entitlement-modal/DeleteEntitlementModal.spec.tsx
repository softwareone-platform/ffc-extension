import { render } from "@testing-library/react";

import { makeEntitlement, triggerModalCancel, triggerModalSubmit } from "~test-utils";
import {
  mockInlineErrorNotification,
  mockSharedInlineErrorNotification,
} from "~test-utils/mocks/inlineErrorNotification";
import { mockModal, mockSharedModal } from "~test-utils/mocks/modal";

import type { useEntitlementController } from "../hooks/useEntitlementsController";
import { DeleteEntitlementModal } from "./DeleteEntitlementModal";

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

describe("DeleteEntitlementModal", () => {
  const entitlement = makeEntitlement({ id: "ent-1" });

  it("passes onClose to the entitlement controller", () => {
    primeController();
    const onClose = jest.fn();

    render(<DeleteEntitlementModal isOpen onClose={onClose} entitlement={entitlement} />);

    expect(mockUseEntitlementController).toHaveBeenCalledWith({ onClose });
  });

  it("shows the controller error in the inline notification", () => {
    primeController({ error: "boom" });

    render(<DeleteEntitlementModal isOpen onClose={jest.fn()} entitlement={entitlement} />);

    expect(mockInlineErrorNotification).toHaveBeenLastCalledWith({ error: "boom" });
  });

  it("shows the submitting state while remove is pending", () => {
    primeController({ isPendingRemove: true });

    render(<DeleteEntitlementModal isOpen onClose={jest.fn()} entitlement={entitlement} />);

    expect(mockModal).toHaveBeenCalledWith(expect.objectContaining({ isSubmitting: true }));
  });

  it("removes the entitlement and calls onSuccess after submit", async () => {
    const remove = jest.fn().mockResolvedValue(undefined);
    primeController({ remove });
    const onSuccess = jest.fn();

    render(
      <DeleteEntitlementModal
        isOpen
        onClose={jest.fn()}
        entitlement={entitlement}
        onSuccess={onSuccess}
      />,
    );
    await triggerModalSubmit(mockModal);

    expect(remove).toHaveBeenCalledWith(entitlement);
    expect(onSuccess).toHaveBeenCalledTimes(1);
  });

  it("does not call remove when no entitlement is provided", async () => {
    const remove = jest.fn();
    primeController({ remove });

    render(<DeleteEntitlementModal isOpen onClose={jest.fn()} entitlement={null} />);
    await triggerModalSubmit(mockModal);

    expect(remove).not.toHaveBeenCalled();
  });

  it("cancels through the entitlement controller when the modal is closed", () => {
    const controller = primeController();

    render(<DeleteEntitlementModal isOpen onClose={jest.fn()} entitlement={entitlement} />);
    triggerModalCancel(mockModal);

    expect(controller.cancel).toHaveBeenCalledTimes(1);
  });
});
