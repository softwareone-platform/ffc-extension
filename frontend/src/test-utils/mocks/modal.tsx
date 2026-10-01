import type { ComponentProps } from "react";

import type { Modal } from "~shared/components/modal/Modal";

type MockModalProps = ComponentProps<typeof Modal>;

export const mockModal = jest.fn() as jest.MockedFunction<(props: MockModalProps) => void>;

export const mockSharedModal = {
  Modal: (props: MockModalProps) => {
    mockModal(props);
    return <div data-testid="modal">{props.children}</div>;
  },
};
