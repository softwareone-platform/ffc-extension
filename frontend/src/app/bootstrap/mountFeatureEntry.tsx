import { ReactNode } from "react";

import { BrowserRouter } from "react-router-dom";

import { mount } from "./mount";

import "./mountFeatureEntry.scss";

export function mountFeatureEntry(routes: ReactNode) {
  mount(routes, false);
}
