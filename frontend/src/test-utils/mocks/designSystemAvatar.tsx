import type { ComponentProps } from "react";

import type { Avatar } from "@swo/design-system/avatar";

type MockAvatarProps = Pick<ComponentProps<typeof Avatar>, "text" | "imageSrc" | "jdenticonValue">;

export const mockDesignSystemAvatar = {
  Avatar: ({ text, imageSrc, jdenticonValue }: MockAvatarProps) => (
    <span data-testid="avatar" data-image-src={imageSrc} data-jdenticon-value={jdenticonValue}>
      {text}
    </span>
  ),
};
