import { ReactNode } from "react";

import { BrowserRouter, Routes } from "react-router-dom";

import { AppProviders } from "./AppProviders";
import { mount } from "./mount";

import "./MountFeatureEntry.scss";

export function mountFeatureEntry(routes: ReactNode) {
  mount(
    <AppProviders>
      <BrowserRouter>
        <Routes>{routes}</Routes>
      </BrowserRouter>
    </AppProviders>,
  );
}
