import { PropsWithChildren, useEffect, useMemo, useState } from 'react';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
// import "../styles.scss";
import type { i18n } from 'i18next';
import { I18nextProvider } from 'react-i18next';

import { DesignSystemOptionsProvider, type LanguageCode } from '@swo/design-system/utils';
import { StatusChipLocalisationProvider } from '@swo/mp-status-chip/context';

import { MPTContextProvider } from '~shared/providers/MPTContextProvider';

// import { i18n } from "~i18n/translations";

type RegionalSettings = {
    dateFormat: string;
    timeFormat: string;
    timeZone: string;
    firstDayOfWeek: number;
};

const STALE_TIME = 5000;
// const STALE_TIME = 1000 * 60 * 5;

const LANGUAGE: LanguageCode = 'en-US';

const REGIONAL_SETTINGS: RegionalSettings = {
    dateFormat: "d MMM yyyy",
    timeFormat: 'HH:mm:ss',
    timeZone: 'UTC',
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

export function ExtensionsProvider({ children, i18n }: PropsWithChildren & { i18n: i18n }) {
    const [isLoaded, setIsLoaded] = useState(false);

    const providerValue = useMemo(() => ({ languageCode: LANGUAGE, ...REGIONAL_SETTINGS }), []);

    useEffect(() => {
        async function run() {
            console.log(`Setting language to ${LANGUAGE}`);

            await i18n.changeLanguage(LANGUAGE);

            setIsLoaded(true);
        }

        run();
    }, [i18n]);

    if (!isLoaded) {
        return <></>;
    }

    return (
        <QueryClientProvider client={queryClient}>
            <DesignSystemOptionsProvider value={providerValue}>
                <StatusChipLocalisationProvider languageCode={LANGUAGE}>
                    <I18nextProvider i18n={i18n}>
                        <MPTContextProvider>{children}</MPTContextProvider>
                    </I18nextProvider>
                </StatusChipLocalisationProvider>
            </DesignSystemOptionsProvider>
        </QueryClientProvider>
    );
}
