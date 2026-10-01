import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { makeEmployee } from "~test-utils";

import {
  mockCreateUserModal,
  mockMakeAdminModal,
  mockUseGridConfig,
  mockUseIsAddUserAllowed,
  mockUseNotifyParentChildModal,
} from "./UsersGrid.spec.mocks";

import { UsersGrid } from "./UsersGrid";
import type { useGridConfig } from "./UsersGrid.config";

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
