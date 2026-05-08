import { Outlet } from 'react-router-dom';

import { i18n } from '~i18n/translations';
import { ExtensionsProvider } from '~shared/providers/extensions-provider';

import '~styles/global.scss';

export function AppShell() {
    return (
        <ExtensionsProvider i18n={i18n}>
            <div className="entitlements-app">
                <Outlet />
            </div>
        </ExtensionsProvider>
    );
}
