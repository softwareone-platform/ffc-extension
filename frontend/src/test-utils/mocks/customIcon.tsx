import type { ComponentProps } from "react";

import type CustomIcon from "~shared/components/custom-icons/CustomIcon";

type MockCustomIconProps = Pick<ComponentProps<typeof CustomIcon>, "name">;

export const mockCustomIcon = {
  __esModule: true,
  default: ({ name }: MockCustomIconProps) => <div data-testid="custom-icon">{name}</div>,
};
