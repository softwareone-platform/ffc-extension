import { ReactNode } from "react";

import { mount } from "./mount";

import "./MountModalEntry.scss";

export function mountModalEntry(modal: ReactNode) {
  mount(modal);
}
