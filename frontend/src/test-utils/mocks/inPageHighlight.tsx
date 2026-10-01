/* eslint-disable react-refresh/only-export-components */
import type { ComponentProps, ReactNode } from "react";

type MockInPageHighlightProps = ComponentProps<
  typeof import("@swo/design-system/in-page-highlight").InPageHighlight
>;
type MockInPageHighlightItemProps = ComponentProps<
  typeof import("@swo/design-system/in-page-highlight").InPageHighlight.Item
>;

const InPageHighlight = ({ children }: MockInPageHighlightProps) => (
  <div data-testid="in-page-highlight">{children}</div>
);
InPageHighlight.Item = ({ children, title }: MockInPageHighlightItemProps) => (
  <div data-testid="highlight-item">
    <span data-testid="highlight-title">{title as ReactNode}</span>
    <span data-testid="highlight-value">{children}</span>
  </div>
);

export const mockDesignSystemInPageHighlight = { InPageHighlight };
