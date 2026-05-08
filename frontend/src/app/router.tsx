import { createHashRouter, redirect } from 'react-router-dom';

/**
 * Lazy adapter: turn a `import('...')` of a feature module + a named export
 * into the `{ Component }` shape react-router's `lazy` expects.
 *
 * Lets us point routes directly at feature components without a `routes/`
 * indirection layer, while keeping per-route code-splitting.
 */
const lazyComponent =
    <K extends string>(importer: () => Promise<Record<K, React.ComponentType>>, exportName: K) =>
    async () => ({ Component: (await importer())[exportName] });

/**
 * Application route tree. URL → component wiring lives here; each `lazy`
 * call code-splits the target module.
 */
export const router = createHashRouter([
    {
        path: '/',
        lazy: lazyComponent(() => import('~app/app-shell'), 'AppShell'),
        children: [
            { index: true, loader: () => redirect('/entitlements') },
            {
                path: 'entitlements',
                lazy: lazyComponent(
                    () => import('~features/entitlements/entitlements-grid'),
                    'default' as never,
                ),
            },
            {
                path: 'organizations',
                children: [
                    {
                        index: true,
                        lazy: lazyComponent(
                            () => import('~features/organizations/list/organizations-grid'),
                            'OrganizationsGrid',
                        ),
                    },
                    {
                        path: ':organizationId',
                        // Hide the parent AppNav while inside the Details layout.
                        handle: { hideAppNav: true },
                        lazy: lazyComponent(
                            () => import('~features/organizations/details/details-layout'),
                            'OrganizationDetailsLayout',
                        ),
                        children: [
                            { index: true, loader: () => redirect('general') },
                            {
                                path: 'general',
                                lazy: lazyComponent(
                                    () => import('~features/organizations/details/general'),
                                    'OrganizationGeneralDetails',
                                ),
                            },
                            {
                                path: 'data-sources',
                                lazy: lazyComponent(
                                    () =>
                                        import('~features/organizations/details/data-sources/data-sources'),
                                    'OrganizationDataSources',
                                ),
                            },
                            {
                                path: 'users',
                                lazy: lazyComponent(
                                    () => import('~features/organizations/details/users/users'),
                                    'OrganizationUsers',
                                ),
                            },
                        ],
                    },
                ],
            },
        ],
    },
]);
