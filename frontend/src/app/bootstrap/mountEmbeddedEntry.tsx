import { ReactNode } from "react";

import { mount } from "./mount";

import "./mountEmbeddedEntry.scss";

export function mountEmbeddedEntry(node: ReactNode) {
  mount(node, false);
}
