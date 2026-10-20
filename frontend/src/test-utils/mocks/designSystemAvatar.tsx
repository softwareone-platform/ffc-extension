import type { ComponentProps } from "react";

import type { Avatar } from "@swo/design-system/avatar";

type MockAvatarProps = Pick<ComponentProps<typeof Avatar>, "text" | "imageSrc">;

export const mockDesignSystemAvatar = {
  Avatar: ({ text, imageSrc }: MockAvatarProps) => (
    <span data-testid="avatar" data-image-src={imageSrc}>
      {text}
    </span>
  ),
};
