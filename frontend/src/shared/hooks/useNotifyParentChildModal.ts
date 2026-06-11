import { useEffect } from "react";

// Notifies the embedding parent window that a child modal opened or closed.
// Used when this app runs inside an iframe (e.g. iframe-as-extension) so the
// host can react — typically to dim/disable interactions while a modal is up.
export function useNotifyParentChildModal(isOpen: boolean) {
  useEffect(() => {
    if (window.parent && window.parent !== window) {
      window.parent.postMessage({ type: "child-modal", isOpen }, "*");
    }
  }, [isOpen]);
}
