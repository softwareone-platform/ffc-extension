import type { ComponentProps, ReactNode } from "react";

import { mockDesignSystemGrid } from "~test-utils/mocks/designSystemGrid";

import type { CreateEntitlementWizard } from "../create-entitlement-wizard/CreateEntitlementWizard";
import type { useGridConfig } from "./EntitlementsGrid.config";
import type { DeleteEntitlementModal } from "./delete-entitlement-modal/DeleteEntitlementModal";
import type { TerminateEntitlementModal } from "./terminate-entitlement-modal/TerminateEntitlementModal";

export type MockCreateWizardProps = ComponentProps<typeof CreateEntitlementWizard>;
export type MockTerminateModalProps = ComponentProps<typeof TerminateEntitlementModal>;
export type MockDeleteModalProps = ComponentProps<typeof DeleteEntitlementModal>;

export const mockUseGridConfig = jest.fn() as jest.MockedFunction<typeof useGridConfig>;
export const mockCreateWizard = jest.fn() as jest.MockedFunction<
  (props: MockCreateWizardProps) => void
>;
export const mockTerminateModal = jest.fn() as jest.MockedFunction<
  (props: MockTerminateModalProps) => void
>;
export const mockDeleteModal = jest.fn() as jest.MockedFunction<
  (props: MockDeleteModalProps) => void
>;
export const mockUseNotifyParentChildModal = jest.fn();

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

