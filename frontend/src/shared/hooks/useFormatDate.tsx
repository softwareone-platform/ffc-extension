import { useCallback } from "react";

import { NO_VALUE, useLocalisation } from "@swo/design-system/utils";

import { getNumberOrZero } from "~shared/utils/NumberUtils";

export function useFormatDate() {
  const { formatDate } = useLocalisation();
  return useCallback(
    (value: string | Date) => {
      const date =
        typeof value === "string" ? new Date(value) : value instanceof Date ? value : null;
      if (getNumberOrZero(date?.getFullYear()) < 1800 || !date || isNaN(date.getTime())) {
        return NO_VALUE;
      }
      return formatDate(date);
    },
    [formatDate],
  );
}
