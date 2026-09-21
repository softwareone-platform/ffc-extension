import { useMemo } from "react";

import { useUserRole } from "./useUserRole";

export function useGridIdentity(id: string, isToUseStorageParameters = true) {
  const { role, user } = useUserRole();
  const userId = user?.user?.id || "unknown";

  return useMemo(
    () => ({
      id: `ffc-extension__${id}--${role}`,
      memoizeId: `ffc-extension__${id}--${role}`,
      storageParameters: isToUseStorageParameters ? [userId] : undefined,
    }),
    [id, isToUseStorageParameters, role, userId],
  );
}
