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
        lazy: lazyComponent(() => import('~app/AppShell'), 'AppShell'),
        children: [
            { index: true, loader: () => redirect('/entitlements') },
            {
                // Top-level layout: renders the shared PageShell (Entitlements /
                // Organizations tabs + "Add organization" action) for list pages.
                lazy: lazyComponent(() => import('~app/layouts'), 'MainLayout'),
                children: [
                    {
                        path: 'entitlements',
                        lazy: lazyComponent(
                            () => import('~features/entitlements/EntitlementsGrid'),
                            'default' as never,
                        ),
                    },
                    {
                        path: 'organizations',
                        lazy: lazyComponent(
                            () => import('~features/organizations/list/OrganizationsGrid'),
                            'OrganizationsGrid',
                        ),
                    },
                ],
            },
            {
                path: 'organizations/:organizationId',
                lazy: lazyComponent(
                    () => import('~features/organizations/details/DetailsLayout'),
                    'OrganizationDetailsLayout',
                ),
                children: [
                    { index: true, loader: () => redirect('general') },
                    {
                        path: 'general',
                        lazy: lazyComponent(
                            () => import('~features/organizations/details/general/General'),
                            'OrganizationGeneralDetails',
                        ),
                    },
                    {
                        path: 'data-sources',
                        lazy: lazyComponent(
                            () =>
                                import('~features/organizations/details/data-sources/DataSources'),
                            'OrganizationDataSources',
                        ),
                    },
                    {
                        path: 'users',
                        lazy: lazyComponent(
                            () => import('~features/organizations/details/users/Users'),
                            'OrganizationUsers',
                        ),
                    },
                ],
            },
        ],
    },
]);
