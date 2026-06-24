import { PropsWithChildren } from "react";

import { i18n } from "~i18n/translations";
import { ExtensionsProvider } from "~shared/providers/ExtensionsProvider";

export function AppProviders({ children }: PropsWithChildren) {
  return <ExtensionsProvider i18n={i18n}>{children}</ExtensionsProvider>;
}
