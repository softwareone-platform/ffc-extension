import type { ComponentProps, MouseEventHandler } from "react";

import type { Button } from "@swo/design-system/button";

export type MockButtonProps = ComponentProps<typeof Button>;

export const mockButton = jest.fn() as jest.MockedFunction<(props: MockButtonProps) => void>;

export const mockDesignSystemButton = {
  Button: (props: MockButtonProps) => {
    mockButton(props);

    const testId =
      "testId" in props && typeof props.testId === "string" ? props.testId : "design-system-button";

    return (
      <button
        data-testid={testId}
        onClick={props.onClick as MouseEventHandler<HTMLButtonElement> | undefined}
        disabled={props.isDisabled}
        data-busy={String(Boolean(props.isBusy))}
        data-color={props.color}
        data-type={props.type}
      >
        {props.children}
      </button>
    );
  },
  ButtonColor: {},
};
