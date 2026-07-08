import { createContext, PropsWithChildren, useEffect, useMemo, useState } from "react";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
// import "../styles.scss";
import type { i18n } from "i18next";
import { I18nextProvider } from "react-i18next";
import { BrowserRouter } from "react-router-dom";

import { DesignSystemOptionsProvider, type LanguageCode } from "@swo/design-system/utils";
import { StatusChipLocalisationProvider } from "@swo/mp-status-chip/context";

import { MPTContextProvider } from "~shared/providers/MPTContextProvider";

import { ErrorHandlerProvider } from "./ErrorHandlerProvider";
import { UserProvider } from "./UserProvider";

// import { i18n } from "~i18n/translations";

type RegionalSettings = {
  dateFormat: string;
  timeFormat: string;
  timeZone: string;
  firstDayOfWeek: number;
};

const STALE_TIME = 5000;
// const STALE_TIME = 1000 * 60 * 5;

const LANGUAGE: LanguageCode = "en-US";

const REGIONAL_SETTINGS: RegionalSettings = {
  dateFormat: "d MMM yyyy",
  timeFormat: "HH:mm:ss",
  timeZone: "UTC",
  firstDayOfWeek: 0,
};

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: STALE_TIME,
      retry: false,
      refetchOnWindowFocus: false,
      refetchOnReconnect: false,
    },
    mutations: { retry: false },
  },
});

export const ExtensionsProviderContext = createContext<{ isStandalone: boolean }>({
  isStandalone: false,
});

export function ExtensionsProvider({
  children,
  i18n,
  isStandalone,
}: PropsWithChildren & { i18n: i18n; isStandalone: boolean }) {
  const [isLoaded, setIsLoaded] = useState(false);

  const providerValue = useMemo(() => ({ languageCode: LANGUAGE, ...REGIONAL_SETTINGS }), []);

  useEffect(() => {
    async function run() {
      await i18n.changeLanguage(LANGUAGE);

      setIsLoaded(true);
    }

    run();
  }, [i18n]);

  if (!isLoaded) {
    return <></>;
  }

  return (
    <ExtensionsProviderContext.Provider value={{ isStandalone }}>
      <QueryClientProvider client={queryClient}>
        <UserProvider>
          <DesignSystemOptionsProvider value={providerValue}>
            <StatusChipLocalisationProvider languageCode={LANGUAGE}>
              <BrowserRouter>
                <I18nextProvider i18n={i18n}>
                  <ErrorHandlerProvider>
                    <MPTContextProvider>{children}</MPTContextProvider>
                  </ErrorHandlerProvider>
                </I18nextProvider>
              </BrowserRouter>
            </StatusChipLocalisationProvider>
          </DesignSystemOptionsProvider>
        </UserProvider>
      </QueryClientProvider>
    </ExtensionsProviderContext.Provider>
  );
}
