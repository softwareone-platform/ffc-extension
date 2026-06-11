import { createRoot } from "react-dom/client";

import { setup } from "@mpt-extension/sdk";

import "~app/bootstrap/MountModalEntry.scss";

import CreateUserModal from "~features/modal/AddUserModal";
import { i18n } from "~i18n/translations";
import { ExtensionsProvider } from "~shared/providers/ExtensionsProvider";

setup((element: Element) => {
  const root = createRoot(element);
  root.render(
    <ExtensionsProvider i18n={i18n}>
      <CreateUserModal />
    </ExtensionsProvider>,
  );
});
