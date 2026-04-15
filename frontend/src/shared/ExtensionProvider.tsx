import { I18nextProvider } from "react-i18next";
import { PropsWithChildren, useEffect, useMemo, useState } from "react";
import { StatusChipLocalisationProvider } from "@swo/mp-status-chip/context";
// import "../styles.scss";
import type { i18n } from "i18next";

import {
  DesignSystemOptionsProvider,
  type LanguageCode,
} from "@swo/design-system/utils";
// import { i18n } from "../../i18n/translations";

type RegionalSettings = {
  dateFormat: string;
  timeFormat: string;
  timeZone: string;
  firstDayOfWeek: number;
};

export function ExtensionsProvider({
  children,
  i18n,
}: PropsWithChildren & { i18n: i18n }) {
  const [isLoaded, setIsLoaded] = useState(false);
  const language: LanguageCode = "en-US";
  const regionalSettings: RegionalSettings = {
    dateFormat: "MM/DD/YYYY",
    timeFormat: "HH:mm:ss",
    timeZone: "UTC",
    firstDayOfWeek: 0,
  };

  const providerValue = useMemo(
    () => ({ languageCode: language, ...regionalSettings }),
    [language, regionalSettings],
  );

  useEffect(() => {
    async function run() {
      if (!language) {
        return;
      }

      console.log(`Setting language to ${language}`);

      await i18n.changeLanguage(language);

      setIsLoaded(true);
    }

    run();
  }, [i18n, language]);

  if (!isLoaded || !language) {
    return <></>;
  }

  return (
    <DesignSystemOptionsProvider value={providerValue}>
      <StatusChipLocalisationProvider languageCode={language}>
        <I18nextProvider i18n={i18n}>{children}</I18nextProvider>
      </StatusChipLocalisationProvider>
    </DesignSystemOptionsProvider>
  );
}
