import React from "react";

import { AvatarProps } from "@swo/design-system/avatar";
import { Navigation } from "@swo/design-system/navigation";

export type PageShellNavItem = {
  path: string;
  label: string;
};

export type PageShellProps = {
  className?: string;
  children?: React.ReactNode;
};

type PageShellHeaderBaseProps = {
  actions?: React.ReactNode;
};

type PageShellHeaderTabsProps = PageShellHeaderBaseProps & {
  items: PageShellNavItem[];
  title?: never;
  subtitle?: never;
  backUrl?: never;
  avatar?: never;
};

type PageShellHeaderTitleProps = PageShellHeaderBaseProps & {
  title: string | React.ReactElement;
  subtitle?: string | React.ReactElement;
  backUrl?: string | null;
  avatar?: AvatarProps;
  items?: never;
};

export type PageShellHeaderProps = PageShellHeaderTabsProps | PageShellHeaderTitleProps;

export type PageShellContentProps = {
  children?: React.ReactNode;
};

/**
 * Page shell with a compound API mirroring `@swo/design-system/navigation`:
 *
 * ```tsx
 * <PageShell>
 *   <PageShell.Header title={...} backUrl={...} avatar={...} actions={...} />
 *   <PageShell.Content>
 *     <Tabs>...</Tabs>
 *   </PageShell.Content>
 * </PageShell>
 * ```
 *
 * `PageShell.Header` accepts either `items` (HeaderBar tabs, used by the
 * top-level `MainLayout`) or `title` + optional `backUrl`/`subtitle`/`avatar`
 * (used by entity detail layouts). The two shapes are enforced via a
 * discriminated union so each call site only sees the props valid for its mode.
 *
 * `PageShell.Content` is a thin wrapper around `Navigation.Content` so callers
 * compose freely (single panel, `<Tabs>` widget, etc.).
 */
export const PageShell: React.FC<PageShellProps> & {
  Header: React.FC<PageShellHeaderProps>;
  Content: React.FC<PageShellContentProps>;
} = ({ children }) => {
  return <Navigation>{children}</Navigation>;
};

const PageShellHeader: React.FC<PageShellHeaderProps> = (props) => {
  const actionsNode = props.actions ? (
    <Navigation.HeaderBar.Actions>{props.actions}</Navigation.HeaderBar.Actions>
  ) : null;

  if ("title" in props && props.title !== undefined) {
    const { title, subtitle, backUrl, avatar } = props;
    return (
      <Navigation.HeaderBar
        backUrl={backUrl ?? undefined}
        title={title}
        subtitle={subtitle}
        avatar={avatar}
      >
        {actionsNode}
      </Navigation.HeaderBar>
    );
  }

  return <Navigation.HeaderBar items={props.items}>{actionsNode}</Navigation.HeaderBar>;
};
PageShellHeader.displayName = "PageShell.Header";

const PageShellContent: React.FC<PageShellContentProps> = ({ children }) => (
  <Navigation.Content>{children}</Navigation.Content>
);
PageShellContent.displayName = "PageShell.Content";

PageShell.Header = PageShellHeader;
PageShell.Content = PageShellContent;
