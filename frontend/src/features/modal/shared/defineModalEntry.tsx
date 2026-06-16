import { ComponentType } from "react";

import { mountModalEntry } from "~app/bootstrap/MountModalEntry";

export type ModalCloseResult = {
  success?: boolean;
};

export type ModalEntryProps = {
  onClose?: (result?: ModalCloseResult) => void;
};

export type ModalEntryComponent = ComponentType<ModalEntryProps>;

export function defineModalEntry(Component: ModalEntryComponent): void {
  mountModalEntry(<Component />);
}
