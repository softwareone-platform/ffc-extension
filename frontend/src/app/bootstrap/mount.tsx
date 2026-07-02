import { ReactNode } from "react";

import { createRoot } from "react-dom/client";

import { setup } from "@mpt-extension/sdk";

import { i18n } from "~i18n/translations";
import { ExtensionsProvider } from "~shared/providers/ExtensionsProvider";

export function mount(node: ReactNode) {
  setup((element: Element) => {
    createRoot(element).render(<ExtensionsProvider i18n={i18n}>{node}</ExtensionsProvider>);
  });
}
