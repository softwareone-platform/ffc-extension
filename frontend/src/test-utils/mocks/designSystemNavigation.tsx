import type { ComponentProps } from "react";

type MockNavigationHighlightsProps = ComponentProps<
  typeof import("@swo/design-system/navigation").Navigation.Highlights
>;

export const mockDesignSystemNavigation = {
  Navigation: {
    Highlights: ({ children }: MockNavigationHighlightsProps) => (
      <div data-testid="highlights-root">{children}</div>
    ),
  },
};
