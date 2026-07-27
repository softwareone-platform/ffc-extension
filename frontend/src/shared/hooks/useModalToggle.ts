import { useCallback, useState } from "react";

import { ModalCloseResult } from "~shared/components/modal/types";

type Options = {
  onSuccess?: () => void;
};

export function useModalToggle<T = unknown>({ onSuccess }: Options = {}) {
  const [isOpen, setIsOpen] = useState(false);
  const [data, setData] = useState<T | null>(null);

  const open = useCallback((data?: T) => {
    setData(data ?? null);
    setIsOpen(true);
  }, []);

  const close = useCallback(
    (result?: ModalCloseResult) => {
      setIsOpen(false);
      setData(null);
      if (result?.success) onSuccess?.();
    },
    [onSuccess],
  );

  return { isOpen, open, close, data };
}
