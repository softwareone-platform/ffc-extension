import { useCallback } from "react";

import { formatDistance } from "date-fns";
import { de, enUS } from "date-fns/locale";

import { NO_VALUE, useLocalisation } from "@swo/design-system/utils";

import { getDate } from "~shared/utils/DateUtils";
import { getNumberOrZero } from "~shared/utils/NumberUtils";

const locales = { en: enUS, "en-US": enUS, de };

export function useDateDistance() {
  const { locale } = useLocalisation();
  return useCallback(
    (value: string | Date) => {
      const date = getDate(value);
      if (getNumberOrZero(date?.getFullYear()) < 1800 || !date) {
        return NO_VALUE;
      }

      const localeCode = (locale?.code || "en") as keyof typeof locales;
      return formatDistance(date, new Date(), {
        locale: locales[localeCode] ?? enUS,
        addSuffix: true,
      });
    },
    [locale],
  );
}
