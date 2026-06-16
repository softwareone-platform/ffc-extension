import { useEffect } from "react";

import { useMPTEmit } from "@mpt-extension/sdk-react";

// Notifies the embedding parent window that a child modal opened or closed.
// Used when this app runs inside an iframe (e.g. iframe-as-extension) so the
// host can react — typically to dim/disable interactions while a modal is up.
export function useNotifyParentChildModal(isOpen: boolean) {
  const emit = useMPTEmit();

  useEffect(() => {
    if (globalThis.__MPT__ === undefined) return;
    emit("child-modal", { isOpen });
  }, [emit, isOpen]);
}
