import { useEffect } from "react";

import { useMPTEmit } from "@mpt-extension/sdk-react";

import { useHasMPTHost } from "~shared/providers/MPTContextProvider";

const CHILD_MODAL_EVENT = "child-modal";

// Notifies the embedding parent window that a child modal opened or closed.
// Used when this app runs inside an iframe (e.g. iframe-as-extension) so the
// host can react — typically to dim/disable interactions while a modal is up.
export function useNotifyParentChildModal(isOpen: boolean) {
  const emit = useMPTEmit();
  const hasHost = useHasMPTHost();

  // Effect cleanup emits the matching `false` on close and on unmount, so the
  // parent overlay never gets stuck if the iframe is torn down while open.
  useEffect(() => {
    if (!hasHost || !isOpen) return;
    emit(CHILD_MODAL_EVENT, { isOpen: true });
    return () => emit(CHILD_MODAL_EVENT, { isOpen: false });
  }, [emit, isOpen, hasHost]);
}
