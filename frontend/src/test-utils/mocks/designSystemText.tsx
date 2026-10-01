import type { ReactNode } from "react";

// Pass-through mocks for @swo/design-system/text so specs can render children
// without pulling in the design-system runtime. All three components collapse to
// their children — the presentational styling is not what's under test.

export const mockDesignSystemText = {
  BoldText: ({ children }: { children?: ReactNode }) => <>{children}</>,
  MediumText: ({ children }: { children?: ReactNode }) => <span>{children}</span>,
  RegularText: ({ children }: { children?: ReactNode }) => <>{children}</>,
};
