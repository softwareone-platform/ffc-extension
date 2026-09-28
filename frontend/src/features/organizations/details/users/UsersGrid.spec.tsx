import type { ComponentProps, ReactNode } from "react";

import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { makeEmployee } from "~test-utils";
import { mockDesignSystemButton } from "~test-utils/mocks/designSystemButton";
import { mockDesignSystemGrid } from "~test-utils/mocks/designSystemGrid";

import type { useIsUserAddAllowed } from "./hooks/useIsAddUserAllowed";
import type { UserMakeAdminModal } from "./make-admin-modal/UserMakeAdminModal";
import type { CreateUserModal } from "./modal/CreateUserModal";
import { UsersGrid } from "./UsersGrid";
import type { useGridConfig } from "./UsersGrid.config";

type MockCreateUserModalProps = ComponentProps<typeof CreateUserModal>;
type MockMakeAdminModalProps = ComponentProps<typeof UserMakeAdminModal>;

const mockUseGridConfig = jest.fn() as jest.MockedFunction<typeof useGridConfig>;
const mockCreateUserModal = jest.fn() as jest.MockedFunction<
  (props: MockCreateUserModalProps) => void
>;
const mockMakeAdminModal = jest.fn() as jest.MockedFunction<
  (props: MockMakeAdminModalProps) => void
>;
const mockUseIsAddUserAllowed = jest.fn() as jest.MockedFunction<typeof useIsUserAddAllowed>;
const mockUseNotifyParentChildModal = jest.fn();

jest.mock("@swo/design-system/grid", () => ({
  ...mockDesignSystemGrid,
  Grid: Object.assign(
    ({ children }: { children?: ReactNode }) => <div data-testid="grid">{children}</div>,
    {
      Actions: ({ children }: { children?: ReactNode }) => (
        <div data-testid="grid-actions">{children}</div>
      ),
    },
  ),
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

function primeConfig() {
  mockUseGridConfig.mockReturnValue({
    refresh: jest.fn(),
    silentRefresh: jest.fn(),
    onEvent: jest.fn(),
  } as unknown as ReturnType<typeof useGridConfig>);
}

function getOnAction() {
  return mockUseGridConfig.mock.lastCall![1]!;
}

describe("UsersGrid", () => {
  beforeEach(() => {
    primeConfig();
    mockUseIsAddUserAllowed.mockReturnValue({ isAddUserAllowed: true });
  });

  it("calls useGridConfig with organizationId and an onAction handler", () => {
    render(<UsersGrid organizationId="org-abc" />);

    expect(mockUseGridConfig).toHaveBeenCalledWith("org-abc", expect.any(Function));
  });

  it("renders an add-user button when isAddUserAllowed is true", () => {
    render(<UsersGrid organizationId="org-abc" />);

    expect(screen.getByTestId("add-user-button")).toBeInTheDocument();
  });

  it("hides the add-user button when isAddUserAllowed is false", () => {
    mockUseIsAddUserAllowed.mockReturnValue({ isAddUserAllowed: false });

    render(<UsersGrid organizationId="org-abc" />);

    expect(screen.queryByTestId("add-user-button")).not.toBeInTheDocument();
  });

  it("opens the create-user modal when the add-user button is clicked", async () => {
    render(<UsersGrid organizationId="org-abc" />);

    await userEvent.click(screen.getByTestId("add-user-button"));

    expect(mockCreateUserModal.mock.lastCall![0]).toMatchObject({
      isOpen: true,
      organizationId: "org-abc",
    });
  });

  it("opens the make-admin modal with the selected employee when onAction fires 'make_admin'", () => {
    render(<UsersGrid organizationId="org-abc" />);
    const item = makeEmployee({ id: "emp-1" });

    act(() => getOnAction()("make_admin", item, jest.fn()));

    expect(mockMakeAdminModal.mock.lastCall![0]).toMatchObject({
      isOpen: true,
      employee: item,
      organizationId: "org-abc",
    });
  });

  it("ignores unknown actions", () => {
    render(<UsersGrid organizationId="org-abc" />);

    act(() => getOnAction()("delete", makeEmployee(), jest.fn()));

    expect(mockMakeAdminModal.mock.lastCall![0].isOpen).toBe(false);
  });

  it("passes addUserModal.isOpen to useNotifyParentChildModal", () => {
    render(<UsersGrid organizationId="org-abc" />);

    expect(mockUseNotifyParentChildModal).toHaveBeenLastCalledWith(false);
  });
});
