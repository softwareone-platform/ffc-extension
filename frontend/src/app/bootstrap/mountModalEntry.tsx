import { ReactNode } from "react";

import { mount } from "./mount";

import "./mountModalEntry.scss";

export function mountModalEntry(modal: ReactNode) {
  mount(modal);
}
