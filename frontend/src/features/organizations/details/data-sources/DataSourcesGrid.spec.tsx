import { act, render, screen } from "@testing-library/react";

import { mockDesignSystemGrid } from "~test-utils/mocks/designSystemGrid";

import { DataSourcesGrid } from "./DataSourcesGrid";

jest.mock("@swo/design-system/grid", () => mockDesignSystemGrid);

const mockUseGridConfig = jest.fn();
jest.mock("./DataSourcesGrid.config", () => ({
  useGridConfig: (
    ...args: Parameters<typeof import("./DataSourcesGrid.config").useGridConfig>
  ) => mockUseGridConfig(...args),
}));

const mockForceImportModal = jest.fn();
jest.mock("./force-import-modal/DataSourceForceImportModal", () => ({
  DataSourceForceImportModal: (props: unknown) => {
    mockForceImportModal(props);
    return <div data-testid="force-import-modal" />;
  },
}));

describe("DataSourcesGrid", () => {
  const refresh = jest.fn();

  beforeEach(() => {
    mockUseGridConfig.mockReturnValue({
      refresh,
      silentRefresh: jest.fn(),
      onEvent: jest.fn(),
      columns: [{ name: "name" }],
      fields: [{ name: "id" }],
    });
  });

  it("calls useGridConfig with organizationId and an onAction handler", () => {
    render(<DataSourcesGrid organizationId="org-abc" />);

    expect(mockUseGridConfig).toHaveBeenCalledWith("org-abc", expect.any(Function));
  });

  it("renders DataSourceForceImportModal closed by default with the organizationId", () => {
    render(<DataSourcesGrid organizationId="org-abc" />);

    expect(screen.getByTestId("force-import-modal")).toBeInTheDocument();
    expect(mockForceImportModal).toHaveBeenCalledWith(
      expect.objectContaining({
        isOpen: false,
        datasource: null,
        organizationId: "org-abc",
        className: "force-import-modal",
      }),
    );
  });

  it("opens the force-import modal with the item when onAction fires 'force_import'", () => {
    render(<DataSourcesGrid organizationId="org-abc" />);
    const onAction = mockUseGridConfig.mock.lastCall![1];
    const item = { id: "ds-1", name: "AWS", type: "aws" };

    act(() => {
      onAction("force_import", item);
    });

    expect(mockForceImportModal.mock.lastCall![0]).toMatchObject({
      isOpen: true,
      datasource: item,
      organizationId: "org-abc",
    });
  });

  it("closes the force-import modal when its onClose fires", () => {
    render(<DataSourcesGrid organizationId="org-abc" />);
    const onAction = mockUseGridConfig.mock.lastCall![1];
    const item = { id: "ds-1", name: "AWS", type: "aws" };
    act(() => onAction("force_import", item));
    expect(mockForceImportModal.mock.lastCall![0].isOpen).toBe(true);

    const onClose = mockForceImportModal.mock.lastCall![0].onClose;
    act(() => onClose());

    expect(mockForceImportModal.mock.lastCall![0].isOpen).toBe(false);
  });

  it("ignores unknown actions", () => {
    render(<DataSourcesGrid organizationId="org-abc" />);
    const onAction = mockUseGridConfig.mock.lastCall![1];

    act(() => {
      onAction("unsupported_action", { id: "ds-2" });
    });

    expect(mockForceImportModal.mock.lastCall![0].isOpen).toBe(false);
  });
});
