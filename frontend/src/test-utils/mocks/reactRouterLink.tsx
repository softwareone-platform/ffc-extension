import type { ComponentProps } from "react";

import type { Link } from "react-router-dom";

type MockLinkProps = Pick<ComponentProps<typeof Link>, "to" | "children">;

// Wire from a `.spec.mocks` sibling: if anything requires react-router-dom before this
// module initialises (e.g. the `~test-utils` barrel), an inline factory hits a TDZ error.
// Real react-router-dom with `Link` swapped for a plain anchor, so isolated cells
// render without a Router context and specs can assert the link target via `href`.
export const mockReactRouterLink: Record<string, unknown> = {
  ...jest.requireActual<Record<string, unknown>>("react-router-dom"),
  Link: ({ to, children }: MockLinkProps) => <a href={String(to)}>{children}</a>,
};
