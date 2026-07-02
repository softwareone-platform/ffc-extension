import { ReactNode } from "react";

import { BrowserRouter, Routes } from "react-router-dom";

import { mount } from "./mount";

import "./mountFeatureEntry.scss";

export function mountFeatureEntry(routes: ReactNode) {
  mount(
    <BrowserRouter>
      <Routes>{routes}</Routes>
    </BrowserRouter>,
  );
}
