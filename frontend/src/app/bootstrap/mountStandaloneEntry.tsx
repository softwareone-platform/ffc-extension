import { ComponentProps } from "react";

import { RouterProvider } from "react-router-dom";

import { mount } from "./mount";

import "./mountStandaloneEntry.scss";

type Router = ComponentProps<typeof RouterProvider>["router"];

export function mountStandaloneEntry(router: Router) {
  mount(<RouterProvider router={router} />);
}
