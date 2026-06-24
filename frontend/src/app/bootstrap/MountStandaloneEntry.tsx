import { ComponentProps } from "react";

import { RouterProvider } from "react-router-dom";

import { AppProviders } from "./AppProviders";
import { mount } from "./mount";

import "./MountStandaloneEntry.scss";

type Router = ComponentProps<typeof RouterProvider>["router"];

export function mountStandaloneEntry(router: Router) {
  mount(
    <AppProviders>
      <RouterProvider router={router} />
    </AppProviders>,
  );
}
