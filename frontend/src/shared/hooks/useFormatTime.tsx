import { useCallback } from "react";

import { NO_VALUE, useLocalisation } from "@swo/design-system/utils";

import { getDate } from "~shared/utils/DateUtils";
import { getNumberOrZero } from "~shared/utils/NumberUtils";

export function useFormatTime() {
  const { formatTime } = useLocalisation();
  return useCallback(
    (value: string | Date) => {
      const date = getDate(value);

      if (getNumberOrZero(date?.getFullYear()) < 1800 || !date) {
        return NO_VALUE;
      }

      return formatTime(date);
    },
    [formatTime],
  );
}
