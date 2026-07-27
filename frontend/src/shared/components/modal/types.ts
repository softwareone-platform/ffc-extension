export type ModalCloseResult = {
  success?: boolean;
};

export type ModalControllerProps = {
  onClose?: (result?: ModalCloseResult) => void;
};
