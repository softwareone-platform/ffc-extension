import type { ComponentProps } from "react";

import type { InlineErrorNotification } from "~shared/components/error/InlineErrorNotification";

type MockInlineErrorProps = ComponentProps<typeof InlineErrorNotification>;

export const mockInlineErrorNotification = jest.fn() as jest.MockedFunction<
  (props: MockInlineErrorProps) => void
>;

export const mockSharedInlineErrorNotification = {
  InlineErrorNotification: (props: MockInlineErrorProps) => {
    mockInlineErrorNotification(props);
    return <div data-testid="inline-error" />;
  },
};
