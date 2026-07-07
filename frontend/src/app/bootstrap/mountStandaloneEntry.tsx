import { BrowserRouter } from "react-router-dom";

import { mount } from "./mount";

import "./mountStandaloneEntry.scss";

export function mountStandaloneEntry(routes: React.ReactNode) {
  mount(<BrowserRouter>{routes}</BrowserRouter>);
}
