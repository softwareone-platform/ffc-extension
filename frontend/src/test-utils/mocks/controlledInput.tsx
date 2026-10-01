import type { ComponentProps } from "react";

import type { ControlledInput } from "~shared/components/form/ControlledInput";

type MockControlledInputProps = ComponentProps<typeof ControlledInput>;

export const mockControlledInput = jest.fn() as jest.MockedFunction<
  (props: MockControlledInputProps) => void
>;

export const mockSharedControlledInput = {
  ControlledInput: (props: MockControlledInputProps) => {
    mockControlledInput(props);
    return <input data-testid={`input-${props.name}`} disabled={props.isDisabled} />;
  },
};
