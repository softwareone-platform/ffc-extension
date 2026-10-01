import type { ComponentProps } from "react";

import { act, render, screen } from "@testing-library/react";

import { makeOrganization } from "~test-utils";
import { mockDesignSystemGrid, mockGridProps } from "~test-utils/mocks/designSystemGrid";

import type { DeleteOrganizationModal } from "./delete-organization-modal/DeleteOrganizationModal";
import type { EditOrganizationModal } from "./edit-organization-modal/EditOrganizationModal";
import { OrganizationsGrid } from "./OrganizationsGrid";
import type { useGridConfig } from "./OrganizationsGrid.config";

type MockEditModalProps = ComponentProps<typeof EditOrganizationModal>;
type MockDeleteModalProps = ComponentProps<typeof DeleteOrganizationModal>;
type MockCardProps = ComponentProps<typeof import("@swo/design-system/card").Card>;

const mockUseGridConfig = jest.fn() as jest.MockedFunction<typeof useGridConfig>;
const mockEditModal = jest.fn() as jest.MockedFunction<(props: MockEditModalProps) => void>;
const mockDeleteModal = jest.fn() as jest.MockedFunction<(props: MockDeleteModalProps) => void>;

jest.mock("@swo/design-system/grid", () => mockDesignSystemGrid);
jest.mock("@swo/design-system/card", () => ({
  Card: ({ children }: MockCardProps) => <div data-testid="card">{children}</div>,
}));

jest.mock("./OrganizationsGrid.config", () => ({
  useGridConfig: (...args: Parameters<typeof useGridConfig>) => mockUseGridConfig(...args),
}));

jest.mock("./edit-organization-modal/EditOrganizationModal", () => ({
  EditOrganizationModal: (props: MockEditModalProps) => {
    mockEditModal(props);
    return (
      <div
        data-testid="edit-modal"
        data-open={String(props.isOpen)}
        data-organization-id={props.organization?.id ?? ""}
      />
    );
  },
}));

jest.mock("./delete-organization-modal/DeleteOrganizationModal", () => ({
  DeleteOrganizationModal: (props: MockDeleteModalProps) => {
    mockDeleteModal(props);
    return (
      <div
        data-testid="delete-modal"
        data-open={String(props.isOpen)}
        data-organization-id={props.organization?.id ?? ""}
      />
    );
  },
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

describe("OrganizationsGrid", () => {
  beforeEach(() => {
    primeConfig();
  });

  it("passes grid props from useGridConfig into Grid", () => {
    render(<OrganizationsGrid />);

    expect(mockGridProps).toHaveBeenCalled();
    expect(screen.getByTestId("grid")).toBeInTheDocument();
  });

  it("initially renders both modals closed with null data", () => {
    render(<OrganizationsGrid />);

    expect(screen.getByTestId("edit-modal")).toHaveAttribute("data-open", "false");
    expect(screen.getByTestId("edit-modal")).toHaveAttribute("data-organization-id", "");
    expect(screen.getByTestId("delete-modal")).toHaveAttribute("data-open", "false");
    expect(screen.getByTestId("delete-modal")).toHaveAttribute("data-organization-id", "");
  });

  it("opens the edit modal with the selected organization when onAction fires 'edit'", () => {
    render(<OrganizationsGrid />);
    const item = makeOrganization({ id: "org-edit" });

    act(() => getOnAction()("edit", item, jest.fn()));

    expect(screen.getByTestId("edit-modal")).toHaveAttribute("data-open", "true");
    expect(screen.getByTestId("edit-modal")).toHaveAttribute("data-organization-id", item.id);
    expect(screen.getByTestId("delete-modal")).toHaveAttribute("data-open", "false");
  });

  it("opens the delete modal with the selected organization when onAction fires 'delete'", () => {
    render(<OrganizationsGrid />);
    const item = makeOrganization({ id: "org-del" });

    act(() => getOnAction()("delete", item, jest.fn()));

    expect(screen.getByTestId("delete-modal")).toHaveAttribute("data-open", "true");
    expect(screen.getByTestId("delete-modal")).toHaveAttribute("data-organization-id", item.id);
    expect(screen.getByTestId("edit-modal")).toHaveAttribute("data-open", "false");
  });

  it("ignores unknown actions", () => {
    render(<OrganizationsGrid />);

    act(() => getOnAction()("activate", makeOrganization(), jest.fn()));

    expect(screen.getByTestId("edit-modal")).toHaveAttribute("data-open", "false");
    expect(screen.getByTestId("delete-modal")).toHaveAttribute("data-open", "false");
  });
});
