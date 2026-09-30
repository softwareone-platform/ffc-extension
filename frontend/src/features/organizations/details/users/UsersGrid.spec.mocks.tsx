import type { ComponentProps } from "react";

import { mockDesignSystemButton } from "~test-utils/mocks/designSystemButton";
import { mockDesignSystemGrid } from "~test-utils/mocks/designSystemGrid";
import { mockNotifyParentChildModalModule } from "~test-utils/mocks/notifyParentChildModal";

import type { useIsUserAddAllowed } from "./hooks/useIsAddUserAllowed";
import type { UserMakeAdminModal } from "./make-admin-modal/UserMakeAdminModal";
import type { CreateUserModal } from "./modal/CreateUserModal";
import type { useGridConfig } from "./UsersGrid.config";

export { mockUseNotifyParentChildModal } from "~test-utils/mocks/notifyParentChildModal";

type MockCreateUserModalProps = ComponentProps<typeof CreateUserModal>;
type MockMakeAdminModalProps = ComponentProps<typeof UserMakeAdminModal>;

export const mockUseGridConfig = jest.fn() as jest.MockedFunction<typeof useGridConfig>;
export const mockCreateUserModal = jest.fn() as jest.MockedFunction<
  (props: MockCreateUserModalProps) => void
>;
export const mockMakeAdminModal = jest.fn() as jest.MockedFunction<
  (props: MockMakeAdminModalProps) => void
>;
export const mockUseIsAddUserAllowed = jest.fn() as jest.MockedFunction<typeof useIsUserAddAllowed>;

jest.mock("@swo/design-system/grid", () => mockDesignSystemGrid);
jest.mock("@swo/design-system/button", () => mockDesignSystemButton);
jest.mock("~shared/hooks/useNotifyParentChildModal", () => mockNotifyParentChildModalModule);

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
