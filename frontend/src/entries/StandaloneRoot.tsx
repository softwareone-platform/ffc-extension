import "~fixes/safe-storage";

import { createRoot } from "react-dom/client";

import { setup } from "@mpt-extension/sdk";

import { App } from "~app/App";
import { i18n } from "~i18n/translations";
import { ExtensionsProvider } from "~shared/providers/ExtensionsProvider";

import "./StandaloneRoot.scss";

setup((element: Element) => {
  createRoot(element).render(
    <ExtensionsProvider i18n={i18n}>
      <App />
    </ExtensionsProvider>,
  );
});
