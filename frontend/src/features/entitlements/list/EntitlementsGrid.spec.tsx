import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { makeEntitlement } from "~test-utils";

import {
  mockCreateWizard,
  mockDeleteModal,
  mockTerminateModal,
  mockUseGridConfig,
  mockUseNotifyParentChildModal,
} from "./EntitlementsGrid.spec.mocks";

import { EntitlementsGrid } from "./EntitlementsGrid";
import type { useGridConfig } from "./EntitlementsGrid.config";

function primeConfig() {
  mockUseGridConfig.mockReturnValue({
    refresh: jest.fn(),
    silentRefresh: jest.fn(),
    onEvent: jest.fn(),
  } as unknown as ReturnType<typeof useGridConfig>);
}

function getOnAction() {
  return mockUseGridConfig.mock.lastCall![0]!;
}

describe("EntitlementsGrid", () => {
  beforeEach(() => {
    primeConfig();
  });

  it("opens no modal until an action fires", () => {
    render(<EntitlementsGrid />);

    expect(screen.getByTestId("create-entitlement-wizard")).toHaveAttribute("data-open", "false");
    expect(mockTerminateModal).toHaveBeenLastCalledWith(
      expect.objectContaining({ isOpen: false, entitlement: null }),
    );
    expect(mockDeleteModal).toHaveBeenLastCalledWith(
      expect.objectContaining({ isOpen: false, entitlement: null }),
    );
  });

  it("opens the create-entitlement wizard when the add button is clicked", async () => {
    render(<EntitlementsGrid />);

    await userEvent.click(screen.getByRole("button", { name: "add" }));

    expect(screen.getByTestId("create-entitlement-wizard")).toHaveAttribute("data-open", "true");
  });

  // eslint-disable-next-line jest/expect-expect
  it("opens the terminate modal with the selected item when onAction fires 'terminate'", () => {
    render(<EntitlementsGrid />);
    const item = makeEntitlement({ id: "ent-t" });

    act(() => getOnAction()("terminate", item, jest.fn()));

    expect(mockTerminateModal).toHaveBeenLastCalledWith(
      expect.objectContaining({ isOpen: true, entitlement: item }),
    );
  });

  // eslint-disable-next-line jest/expect-expect
  it("opens the delete modal with the selected item when onAction fires 'delete'", () => {
    render(<EntitlementsGrid />);
    const item = makeEntitlement({ id: "ent-d" });

    act(() => getOnAction()("delete", item, jest.fn()));

    expect(mockDeleteModal).toHaveBeenLastCalledWith(
      expect.objectContaining({ isOpen: true, entitlement: item }),
    );
  });

  it("ignores unknown actions", () => {
    render(<EntitlementsGrid />);

    act(() => getOnAction()("redeem", makeEntitlement(), jest.fn()));

    expect(mockTerminateModal).toHaveBeenLastCalledWith(
      expect.objectContaining({ isOpen: false, entitlement: null }),
    );
    expect(mockDeleteModal).toHaveBeenLastCalledWith(
      expect.objectContaining({ isOpen: false, entitlement: null }),
    );
  });

  it("passes createEntitlementModal.isOpen to useNotifyParentChildModal", () => {
    render(<EntitlementsGrid />);

    expect(mockUseNotifyParentChildModal).toHaveBeenLastCalledWith(false);
  });
});
