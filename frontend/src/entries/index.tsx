import { createRoot } from "react-dom/client";

import { RouterProvider } from "react-router-dom";

import { router } from "~app/router";
import { StandaloneProvider } from "~app/standalone-context";

import "~styles/global-standalone.scss";

import { setup } from "@mpt-extension/sdk";

setup((element: Element) => {
  const root = createRoot(element);
  root.render(
    <StandaloneProvider>
      <RouterProvider router={router} />
    </StandaloneProvider>,
  );
});
