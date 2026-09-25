import type { ComponentProps, ReactNode } from "react";

import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import { makeEntitlement } from "~test-utils";
import { mockDesignSystemGrid } from "~test-utils/mocks/designSystemGrid";

import type { CreateEntitlementWizard } from "../create-entitlement-wizard/CreateEntitlementWizard";
import type { DeleteEntitlementModal } from "./delete-entitlement-modal/DeleteEntitlementModal";
import { EntitlementsGrid } from "./EntitlementsGrid";
import type { useGridConfig } from "./EntitlementsGrid.config";
import type { TerminateEntitlementModal } from "./terminate-entitlement-modal/TerminateEntitlementModal";

type MockCreateWizardProps = ComponentProps<typeof CreateEntitlementWizard>;
type MockTerminateModalProps = ComponentProps<typeof TerminateEntitlementModal>;
type MockDeleteModalProps = ComponentProps<typeof DeleteEntitlementModal>;

const mockUseGridConfig = jest.fn() as jest.MockedFunction<typeof useGridConfig>;
const mockCreateWizard = jest.fn() as jest.MockedFunction<(props: MockCreateWizardProps) => void>;
const mockTerminateModal = jest.fn() as jest.MockedFunction<
  (props: MockTerminateModalProps) => void
>;
const mockDeleteModal = jest.fn() as jest.MockedFunction<(props: MockDeleteModalProps) => void>;
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

jest.mock("@swo/design-system/card", () => ({
  Card: ({ children }: { children?: ReactNode }) => <div data-testid="card">{children}</div>,
}));

jest.mock("@swo/design-system/button", () => ({
  Button: ({ children, onClick }: { children?: ReactNode; onClick?: () => void }) => (
    <button data-testid="add-entitlement-button" onClick={onClick} type="button">
      {children}
    </button>
  ),
}));

jest.mock("./EntitlementsGrid.config", () => ({
  useGridConfig: (...args: Parameters<typeof useGridConfig>) => mockUseGridConfig(...args),
}));

jest.mock("../create-entitlement-wizard/CreateEntitlementWizard", () => ({
  CreateEntitlementWizard: (props: MockCreateWizardProps) => {
    mockCreateWizard(props);
    return <div data-testid="create-entitlement-wizard" />;
  },
}));

jest.mock("./terminate-entitlement-modal/TerminateEntitlementModal", () => ({
  TerminateEntitlementModal: (props: MockTerminateModalProps) => {
    mockTerminateModal(props);
    return <div data-testid="terminate-modal" />;
  },
}));

jest.mock("./delete-entitlement-modal/DeleteEntitlementModal", () => ({
  DeleteEntitlementModal: (props: MockDeleteModalProps) => {
    mockDeleteModal(props);
    return <div data-testid="delete-modal" />;
  },
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
  return mockUseGridConfig.mock.lastCall![0]!;
}

describe("EntitlementsGrid", () => {
  beforeEach(() => {
    primeConfig();
  });

  it("opens no modal until an action fires", () => {
    render(<EntitlementsGrid />);

    expect(mockCreateWizard.mock.lastCall![0]).toMatchObject({ isOpen: false });
    expect(mockTerminateModal.mock.lastCall![0]).toMatchObject({
      isOpen: false,
      entitlement: null,
    });
    expect(mockDeleteModal.mock.lastCall![0]).toMatchObject({
      isOpen: false,
      entitlement: null,
    });
  });

  it("opens the create-entitlement wizard when the add button is clicked", async () => {
    render(<EntitlementsGrid />);

    await userEvent.click(screen.getByTestId("add-entitlement-button"));

    expect(mockCreateWizard.mock.lastCall![0]).toMatchObject({ isOpen: true });
  });

  it("opens the terminate modal with the selected item when onAction fires 'terminate'", () => {
    render(<EntitlementsGrid />);
    const item = makeEntitlement({ id: "ent-t" });

    act(() => getOnAction()("terminate", item, jest.fn()));

    expect(mockTerminateModal.mock.lastCall![0]).toMatchObject({
      isOpen: true,
      entitlement: item,
    });
  });

  it("opens the delete modal with the selected item when onAction fires 'delete'", () => {
    render(<EntitlementsGrid />);
    const item = makeEntitlement({ id: "ent-d" });

    act(() => getOnAction()("delete", item, jest.fn()));

    expect(mockDeleteModal.mock.lastCall![0]).toMatchObject({
      isOpen: true,
      entitlement: item,
    });
  });

  it("ignores unknown actions", () => {
    render(<EntitlementsGrid />);

    act(() => getOnAction()("redeem", makeEntitlement(), jest.fn()));

    expect(mockTerminateModal.mock.lastCall![0].isOpen).toBe(false);
    expect(mockDeleteModal.mock.lastCall![0].isOpen).toBe(false);
  });

  it("passes createEntitlementModal.isOpen to useNotifyParentChildModal", () => {
    render(<EntitlementsGrid />);

    expect(mockUseNotifyParentChildModal).toHaveBeenLastCalledWith(false);
  });
});
