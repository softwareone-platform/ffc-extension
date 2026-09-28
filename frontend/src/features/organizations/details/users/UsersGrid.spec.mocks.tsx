import type { ComponentProps } from "react";

import { mockDesignSystemButton } from "~test-utils/mocks/designSystemButton";
import { mockDesignSystemGrid } from "~test-utils/mocks/designSystemGrid";

import type { useIsUserAddAllowed } from "./hooks/useIsAddUserAllowed";
import type { UserMakeAdminModal } from "./make-admin-modal/UserMakeAdminModal";
import type { CreateUserModal } from "./modal/CreateUserModal";
import type { useGridConfig } from "./UsersGrid.config";

type MockCreateUserModalProps = ComponentProps<typeof CreateUserModal>;
type MockMakeAdminModalProps = ComponentProps<typeof UserMakeAdminModal>;
type MockGridProps = ComponentProps<typeof import("@swo/design-system/grid").Grid>;
type MockGridActionsProps = ComponentProps<typeof import("@swo/design-system/grid").Grid.Actions>;

export const mockUseGridConfig = jest.fn() as jest.MockedFunction<typeof useGridConfig>;
export const mockCreateUserModal = jest.fn() as jest.MockedFunction<
  (props: MockCreateUserModalProps) => void
>;
export const mockMakeAdminModal = jest.fn() as jest.MockedFunction<
  (props: MockMakeAdminModalProps) => void
>;
export const mockUseIsAddUserAllowed = jest.fn() as jest.MockedFunction<typeof useIsUserAddAllowed>;
export const mockUseNotifyParentChildModal = jest.fn();

jest.mock("@swo/design-system/grid", () => ({
  ...mockDesignSystemGrid,
  Grid: Object.assign(({ children }: MockGridProps) => <div data-testid="grid">{children}</div>, {
    Actions: ({ children }: MockGridActionsProps) => (
      <div data-testid="grid-actions">{children}</div>
    ),
  }),
}));

jest.mock("@swo/design-system/button", () => mockDesignSystemButton);

jest.mock("./UsersGrid.config", () => ({
  useGridConfig: (...args: Parameters<typeof useGridConfig>) => mockUseGridConfig(...args),
}));

jest.mock("./modal/CreateUserModal", () => ({
  CreateUserModal: (props: MockCreateUserModalProps) => {
    mockCreateUserModal(props);
    return <div data-testid="create-user-modal" />;
  },
}));

jest.mock("./make-admin-modal/UserMakeAdminModal", () => ({
  UserMakeAdminModal: (props: MockMakeAdminModalProps) => {
    mockMakeAdminModal(props);
    return <div data-testid="make-admin-modal" />;
  },
}));

jest.mock("./hooks/useIsAddUserAllowed", () => ({
  useIsUserAddAllowed: (id: string) => mockUseIsAddUserAllowed(id),
}));

jest.mock("~shared/hooks/useNotifyParentChildModal", () => ({
  useNotifyParentChildModal: (open: boolean) => mockUseNotifyParentChildModal(open),
}));
