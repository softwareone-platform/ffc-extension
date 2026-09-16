import { act, render, screen } from "@testing-library/react";

import { DataSourcesGrid } from "./DataSourcesGrid";

const mockGridProps = jest.fn();
jest.mock("@swo/design-system/grid", () => ({
  Grid: (props: unknown) => {
    mockGridProps(props);
    return <div data-testid="grid" />;
  },
}));

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
    jest.clearAllMocks();
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

  it("forwards useGridConfig props to Grid (excluding refresh)", () => {
    render(<DataSourcesGrid organizationId="org-abc" />);

    expect(screen.getByTestId("grid")).toBeInTheDocument();
    const gridProps = mockGridProps.mock.calls[0][0];
    expect(gridProps).toMatchObject({
      columns: [{ name: "name" }],
      fields: [{ name: "id" }],
    });
    expect(gridProps).not.toHaveProperty("refresh");
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
    const onAction = mockUseGridConfig.mock.calls[0][1];
    const item = { id: "ds-1", name: "AWS", type: "aws" };

    act(() => {
      onAction("force_import", item);
    });

    const calls = mockForceImportModal.mock.calls;
    const latestCall = calls[calls.length - 1][0];
    expect(latestCall).toMatchObject({
      isOpen: true,
      datasource: item,
      organizationId: "org-abc",
    });
  });

  it("ignores unknown actions", () => {
    render(<DataSourcesGrid organizationId="org-abc" />);
    const onAction = mockUseGridConfig.mock.calls[0][1];

    act(() => {
      onAction("unsupported_action", { id: "ds-2" });
    });

    const calls = mockForceImportModal.mock.calls;
    const latestCall = calls[calls.length - 1][0];
    expect(latestCall.isOpen).toBe(false);
  });
});
