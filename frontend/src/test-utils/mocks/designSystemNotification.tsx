import type { ComponentProps } from "react";

import type { InlineNotification } from "@swo/design-system/notification";

type MockInlineNotificationProps = ComponentProps<typeof InlineNotification>;

export const mockDesignSystemNotification = {
  InlineNotification: ({ children }: MockInlineNotificationProps) => (
    <div data-testid="inline-notification">{children}</div>
  ),
};
