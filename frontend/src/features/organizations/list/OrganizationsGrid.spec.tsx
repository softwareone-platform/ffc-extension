import type { ComponentProps, ReactNode } from "react";

import { act, render, screen } from "@testing-library/react";

import { makeOrganization } from "~test-utils";
import { mockDesignSystemGrid, mockGridProps } from "~test-utils/mocks/designSystemGrid";

import type { DeleteOrganizationModal } from "./delete-organization-modal/DeleteOrganizationModal";
import type { EditOrganizationModal } from "./edit-organization-modal/EditOrganizationModal";
import { OrganizationsGrid } from "./OrganizationsGrid";
import type { useGridConfig } from "./OrganizationsGrid.config";

type MockEditModalProps = ComponentProps<typeof EditOrganizationModal>;
type MockDeleteModalProps = ComponentProps<typeof DeleteOrganizationModal>;

const mockUseGridConfig = jest.fn() as jest.MockedFunction<typeof useGridConfig>;
const mockEditModal = jest.fn() as jest.MockedFunction<(props: MockEditModalProps) => void>;
const mockDeleteModal = jest.fn() as jest.MockedFunction<(props: MockDeleteModalProps) => void>;

jest.mock("@swo/design-system/grid", () => mockDesignSystemGrid);
jest.mock("@swo/design-system/card", () => ({
  Card: ({ children }: { children?: ReactNode }) => <div data-testid="card">{children}</div>,
}));

jest.mock("./OrganizationsGrid.config", () => ({
  useGridConfig: (...args: Parameters<typeof useGridConfig>) => mockUseGridConfig(...args),
}));

jest.mock("./edit-organization-modal/EditOrganizationModal", () => ({
  EditOrganizationModal: (props: MockEditModalProps) => {
    mockEditModal(props);
    return <div data-testid="edit-modal" />;
  },
}));

jest.mock("./delete-organization-modal/DeleteOrganizationModal", () => ({
  DeleteOrganizationModal: (props: MockDeleteModalProps) => {
    mockDeleteModal(props);
    return <div data-testid="delete-modal" />;
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

    expect(mockEditModal.mock.lastCall![0]).toMatchObject({ isOpen: false, organization: null });
    expect(mockDeleteModal.mock.lastCall![0]).toMatchObject({ isOpen: false, organization: null });
  });

  it("opens the edit modal with the selected organization when onAction fires 'edit'", () => {
    render(<OrganizationsGrid />);
    const item = makeOrganization({ id: "org-edit" });

    act(() => getOnAction()("edit", item, jest.fn()));

    expect(mockEditModal.mock.lastCall![0]).toMatchObject({ isOpen: true, organization: item });
    expect(mockDeleteModal.mock.lastCall![0].isOpen).toBe(false);
  });

  it("opens the delete modal with the selected organization when onAction fires 'delete'", () => {
    render(<OrganizationsGrid />);
    const item = makeOrganization({ id: "org-del" });

    act(() => getOnAction()("delete", item, jest.fn()));

    expect(mockDeleteModal.mock.lastCall![0]).toMatchObject({ isOpen: true, organization: item });
    expect(mockEditModal.mock.lastCall![0].isOpen).toBe(false);
  });

  it("ignores unknown actions", () => {
    render(<OrganizationsGrid />);

    act(() => getOnAction()("activate", makeOrganization(), jest.fn()));

    expect(mockEditModal.mock.lastCall![0].isOpen).toBe(false);
    expect(mockDeleteModal.mock.lastCall![0].isOpen).toBe(false);
  });
});
