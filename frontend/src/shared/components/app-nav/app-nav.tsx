import React from 'react';
import { Navigation } from '@swo/design-system/navigation';
import './app-nav.scss';

export type AppNavItem = {
    /** Route path the HeaderBar item points to. */
    path: string;
    /** Visible label rendered inside the nav item. */
    label: string;
};

export type AppNavProps = {
    /** Navigation items rendered as tabs in the HeaderBar. */
    items: AppNavItem[];
    /** Optional content rendered on the right side of the HeaderBar (buttons, etc.). */
    actions?: React.ReactNode;
    /** Routed page content rendered inside Navigation.Content. */
    children?: React.ReactNode;
    /** Optional extra className appended to the wrapper. */
    className?: string;
};

/**
 * Generic, presentation-only application navigation bar.
 *
 * Thin wrapper around `@swo/design-system/navigation` that exposes a simple
 * `items` + `actions` + `children` API. Knows nothing about specific features —
 * feature-specific actions (e.g. "Add organization") are injected via `actions`,
 * and routed page content is passed as `children`.
 */
export const AppNav: React.FC<AppNavProps> = ({ items, actions, children, className }) => {
    return (
        <div className={`app-nav${className ? ` ${className}` : ''}`}>
            <Navigation>
                <Navigation.HeaderBar items={items}>
                    {actions ? (
                        <Navigation.HeaderBar.Actions>{actions}</Navigation.HeaderBar.Actions>
                    ) : null}
                </Navigation.HeaderBar>
                <Navigation.Content>{children}</Navigation.Content>
            </Navigation>
        </div>
    );
};

export default AppNav;
