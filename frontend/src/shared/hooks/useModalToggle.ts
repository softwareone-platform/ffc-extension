import { useCallback, useState } from "react";

import { ModalCloseResult } from "~shared/components/modal/modalEntry";

type Options = {
  onSuccess?: () => void;
};

export function useModalToggle({ onSuccess }: Options = {}) {
  const [isOpen, setIsOpen] = useState(false);

  const open = useCallback(() => setIsOpen(true), []);

  const close = useCallback(
    (result?: ModalCloseResult) => {
      setIsOpen(false);
      if (result?.success) onSuccess?.();
    },
    [onSuccess],
  );

  return { isOpen, open, close };
}
