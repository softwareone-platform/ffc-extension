import { Outlet } from 'react-router-dom';

import { i18n } from '~i18n/translations';
import { ExtensionsProvider } from '~shared/providers/ExtensionsProvider';

import '~styles/global-standalone.scss';

export function AppShell() {
    return (
        <ExtensionsProvider i18n={i18n}>
            <div className="standalone-app">
                <Outlet />
            </div>
        </ExtensionsProvider>
    );
}
