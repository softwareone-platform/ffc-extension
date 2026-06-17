import { ReactNode } from "react";

import { AppProviders } from "./AppProviders";
import { mount } from "./mount";

import "./base.scss";

export function mountModalEntry(modal: ReactNode) {
  mount(<AppProviders>{modal}</AppProviders>);
}
