import type { ComponentProps } from "react";

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import type { UserEvent } from "~test-utils";
import { mockButton, mockDesignSystemButton } from "~test-utils/mocks/designSystemButton";

import { Modal } from "./Modal";
import { ModalCancelButton } from "./ModalCancelButton";

type DSModalProps = ComponentProps<typeof import("@swo/design-system/modal").Modal>;
type CancelButtonProps = ComponentProps<typeof ModalCancelButton>;

const mockDSModal = jest.fn() as jest.MockedFunction<(props: DSModalProps) => void>;
const mockModalCancelButton = jest.fn() as jest.MockedFunction<(props: CancelButtonProps) => void>;

jest.mock("@swo/design-system/modal", () => ({
  Modal: (props: DSModalProps) => {
    mockDSModal(props);
    return (
      <div data-testid="design-system-modal">
        <div data-testid="modal-children">{props.children}</div>
        <div data-testid="modal-actions">{props.actions}</div>
      </div>
    );
  },
}));

jest.mock("@swo/design-system/button", () => mockDesignSystemButton);

jest.mock("./ModalCancelButton", () => ({
  ModalCancelButton: ({ onClick, isDisabled }: CancelButtonProps) => {
    mockModalCancelButton({ onClick, isDisabled });
    return (
      <button data-testid="cancel-button" onClick={onClick} disabled={isDisabled}>
        cancel
      </button>
    );
  },
}));

describe("Modal", () => {
  let user: UserEvent;

  beforeEach(() => {
    user = userEvent.setup();
  });

  it("forwards modal props, children, and merges the wrapper class", () => {
    render(
      <Modal
        isOpen
        onClose={jest.fn()}
        title="Modal title"
        width={720}
        closeOnEsc
        isToCloseOnClickOutside
        isFullScreen
        isToShowCloseButton
        isToHidePadding
        isToShowWarningModal
        testId="modal-id"
        className="custom-class"
      >
        <div>body</div>
      </Modal>,
    );

    expect(screen.getByTestId("modal-children")).toHaveTextContent("body");
    expect(mockDSModal.mock.lastCall?.[0]).toEqual(
      expect.objectContaining({
        isOpen: true,
        title: "Modal title",
        width: 720,
        closeOnEsc: true,
        isToCloseOnClickOutside: true,
        isFullScreen: true,
        isToShowCloseButton: true,
        isToHidePadding: true,
        isToShowWarningModal: true,
        testId: "modal-id",
        className: "wrapped-modal-content custom-class",
      }),
    );
  });

  it("passes custom actions through unchanged", () => {
    render(
      <Modal isOpen onClose={jest.fn()} actions={<div data-testid="custom-actions">custom</div>}>
        <div>body</div>
      </Modal>,
    );

    expect(screen.getByTestId("custom-actions")).toHaveTextContent("custom");
    expect(mockModalCancelButton).not.toHaveBeenCalled();
    expect(mockButton).not.toHaveBeenCalled();
  });

  it("leaves actions undefined when onSubmit is not provided", () => {
    render(
      <Modal isOpen onClose={jest.fn()}>
        <div>body</div>
      </Modal>,
    );

    expect(mockDSModal.mock.lastCall?.[0].actions).toBeUndefined();
  });

  it("builds default actions and uses onClose as the cancel fallback", async () => {
    const onClose = jest.fn();
    const onSubmit = jest.fn();

    render(
      <Modal isOpen onClose={onClose} onSubmit={onSubmit} submitLabel="save">
        <div>body</div>
      </Modal>,
    );

    expect(mockModalCancelButton).toHaveBeenCalledWith({ onClick: onClose, isDisabled: undefined });
    expect(mockButton).toHaveBeenCalledWith(
      expect.objectContaining({
        children: "save",
        color: "primary",
        isDisabled: false,
        isBusy: undefined,
        type: "primary",
      }),
    );

    await user.click(screen.getByTestId("cancel-button"));
    await user.click(screen.getByRole("button", { name: "save" }));

    expect(onClose).toHaveBeenCalledTimes(1);
    expect(onSubmit).toHaveBeenCalledTimes(1);
  });

  it("prefers onCancel over onClose and propagates submitting and disabled states", async () => {
    const onClose = jest.fn();
    const onCancel = jest.fn();
    const onSubmit = jest.fn();

    render(
      <Modal
        isOpen
        onClose={onClose}
        onCancel={onCancel}
        onSubmit={onSubmit}
        submitLabel="save"
        isSubmitting
        isSubmitDisabled
        submitButtonColor="danger"
      >
        <div>body</div>
      </Modal>,
    );

    expect(mockModalCancelButton).toHaveBeenCalledWith({ onClick: onCancel, isDisabled: true });
    expect(screen.getByTestId("cancel-button")).toBeDisabled();
    expect(screen.getByRole("button", { name: "save" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "save" })).toHaveAttribute("data-busy", "true");
    expect(screen.getByRole("button", { name: "save" })).toHaveAttribute("data-color", "danger");

    await user.click(screen.getByRole("button", { name: "save" }));

    expect(onCancel).not.toHaveBeenCalled();
    expect(onClose).not.toHaveBeenCalled();
    expect(onSubmit).not.toHaveBeenCalled();
  });
});
