import type { ComponentProps } from "react";

import { mockDesignSystemButton } from "~test-utils/mocks/designSystemButton";
import { mockDesignSystemGrid } from "~test-utils/mocks/designSystemGrid";

import type { CreateEntitlementWizard } from "../create-entitlement-wizard/CreateEntitlementWizard";
import type { DeleteEntitlementModal } from "./delete-entitlement-modal/DeleteEntitlementModal";
import type { useGridConfig } from "./EntitlementsGrid.config";
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

type GridProps = ComponentProps<typeof import("@swo/design-system/grid").Grid>;
type GridActionsProps = ComponentProps<typeof import("@swo/design-system/grid").Grid.Actions>;
type CardProps = ComponentProps<typeof import("@swo/design-system/card").Card>;

jest.mock("@swo/design-system/grid", () => ({
  ...mockDesignSystemGrid,
  Grid: Object.assign(({ children }: GridProps) => <div data-testid="grid">{children}</div>, {
    Actions: ({ children }: GridActionsProps) => <div data-testid="grid-actions">{children}</div>,
  }),
}));

jest.mock("@swo/design-system/card", () => ({
  Card: ({ children }: CardProps) => <div data-testid="card">{children}</div>,
}));

jest.mock("@swo/design-system/button", () => mockDesignSystemButton);

jest.mock("./EntitlementsGrid.config", () => ({
  useGridConfig: (...args: Parameters<typeof useGridConfig>) => mockUseGridConfig(...args),
}));

jest.mock("../create-entitlement-wizard/CreateEntitlementWizard", () => ({
  CreateEntitlementWizard: (props: MockCreateWizardProps) => {
    mockCreateWizard(props);
    return <div data-testid="create-entitlement-wizard" data-open={String(props.isOpen)} />;
  },
}));

jest.mock("./terminate-entitlement-modal/TerminateEntitlementModal", () => ({
  TerminateEntitlementModal: (props: MockTerminateModalProps) => {
    mockTerminateModal(props);
    return (
      <div
        data-testid="terminate-modal"
        data-open={String(props.isOpen)}
        data-entitlement-id={props.entitlement?.id ?? ""}
      />
    );
  },
}));

jest.mock("./delete-entitlement-modal/DeleteEntitlementModal", () => ({
  DeleteEntitlementModal: (props: MockDeleteModalProps) => {
    mockDeleteModal(props);
    return (
      <div
        data-testid="delete-modal"
        data-open={String(props.isOpen)}
        data-entitlement-id={props.entitlement?.id ?? ""}
      />
    );
  },
}));

jest.mock("~shared/hooks/useNotifyParentChildModal", () => ({
  useNotifyParentChildModal: (open: boolean) => mockUseNotifyParentChildModal(open),
}));
