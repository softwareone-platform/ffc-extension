import { ReactNode } from "react";

import { Button } from "@swo/design-system/button";
import { Modal } from "@swo/design-system/modal";

import { ModalCancelButton } from "./ModalCancelButton";

const DEFAULT_WIDTH = 600;
const DEFAULT_CLASS = "wrapped-modal-content";

type Props = {
  isOpen: boolean;
  onClose: () => void;
  children: ReactNode;
  title?: string;
  className?: string;
  width?: number | string;
  closeOnEsc?: boolean;
  isToCloseOnClickOutside?: boolean;
  isFullScreen?: boolean;
  isToShowCloseButton?: boolean;
  isToHidePadding?: boolean;
  isToShowWarningModal?: boolean;
  testId?: string;
  actions?: ReactNode;
  onCancel?: () => void;
  onSubmit?: () => void;
  submitLabel?: string;
  isSubmitting?: boolean;
};

export function StandaloneModal({
  isOpen,
  onClose,
  children,
  title,
  className,
  width = DEFAULT_WIDTH,
  closeOnEsc,
  isToCloseOnClickOutside,
  isFullScreen,
  isToShowCloseButton,
  isToHidePadding,
  isToShowWarningModal,
  testId,
  actions,
  onCancel,
  onSubmit,
  submitLabel,
  isSubmitting,
}: Props) {
  const mergedClassName = className ? `${DEFAULT_CLASS} ${className}` : DEFAULT_CLASS;
  const resolvedActions = actions ?? buildDefaultActions({ onCancel: onCancel ?? onClose, onSubmit, submitLabel, isSubmitting });

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={title}
      width={width}
      closeOnEsc={closeOnEsc}
      isToCloseOnClickOutside={isToCloseOnClickOutside}
      isFullScreen={isFullScreen}
      isToShowCloseButton={isToShowCloseButton}
      isToHidePadding={isToHidePadding}
      isToShowWarningModal={isToShowWarningModal}
      testId={testId}
      className={mergedClassName}
      actions={resolvedActions}
    >
      {children}
    </Modal>
  );
}

function buildDefaultActions({
  onCancel,
  onSubmit,
  submitLabel,
  isSubmitting,
}: {
  onCancel: () => void;
  onSubmit?: () => void;
  submitLabel?: string;
  isSubmitting?: boolean;
}): ReactNode | undefined {
  if (!onSubmit) return undefined;
  return (
    <>
      <ModalCancelButton onClick={onCancel} isDisabled={isSubmitting} />
      <Button type="primary" onClick={onSubmit} isBusy={isSubmitting}>
        {submitLabel}
      </Button>
    </>
  );
}
