import { ReactNode } from "react";

import { createRoot } from "react-dom/client";

import { setup } from "@mpt-extension/sdk";

export function mount(node: ReactNode) {
  setup((element: Element) => {
    createRoot(element).render(node);
  });
}
