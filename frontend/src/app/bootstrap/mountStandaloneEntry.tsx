import { mount } from "./mount";

import "./mountStandaloneEntry.scss";

export function mountStandaloneEntry(routes: React.ReactNode) {
  mount(routes, true);
}
