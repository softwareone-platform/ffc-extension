import { createRoot } from "react-dom/client";

import EntitlementWizard from "~features/entitlements/create-entitlement-wizard/CreateEntitlement";
import { i18n } from "~i18n/translations";

import "~styles/global.scss";

import { setup } from "@mpt-extension/sdk";

import { ExtensionsProvider } from "~shared/providers/ExtensionsProvider";

setup((element: Element) => {
  const root = createRoot(element);
  root.render(
    <ExtensionsProvider i18n={i18n}>
      <EntitlementWizard />
    </ExtensionsProvider>,
  );
});
