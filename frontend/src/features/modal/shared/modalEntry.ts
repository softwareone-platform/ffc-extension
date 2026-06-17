import { ComponentType } from "react";

export type ModalCloseResult = {
  success?: boolean;
};

export type ModalEntryProps = {
  onClose?: (result?: ModalCloseResult) => void;
};

export type ModalEntryComponent = ComponentType<ModalEntryProps>;
