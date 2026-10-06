import type { ComponentProps, ReactNode } from "react";

import type { Avatar } from "@swo/design-system/avatar";
import type { Icon } from "@swo/design-system/icon";

import { mockDesignSystemButton } from "~test-utils/mocks/designSystemButton";
import { mockDesignSystemEntityReference } from "~test-utils/mocks/entityReference";

type MockAvatarProps = ComponentProps<typeof Avatar>;
type MockIconProps = ComponentProps<typeof Icon>;

jest.mock("@swo/design-system/button", () => mockDesignSystemButton);
jest.mock("@swo/design-system/entity-reference", () => mockDesignSystemEntityReference);
jest.mock("@swo/design-system/avatar", () => ({
  Avatar: ({ text }: MockAvatarProps) => <span data-testid="avatar">{text}</span>,
}));
jest.mock("@swo/design-system/icon", () => ({
  Icon: ({ name }: MockIconProps) => <span data-testid="toggle-icon">{name}</span>,
}));
jest.mock("@swo/design-system/ellipsis", () => ({
  Ellipsis: ({ children }: { children?: ReactNode }) => (
    <span data-testid="event-name">{children}</span>
  ),
}));
