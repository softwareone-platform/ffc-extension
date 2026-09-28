import { act, render, screen } from "@testing-library/react";

import { mockForceImportModal, mockUseGridConfig } from "./DataSourcesGrid.spec.mocks";

import { DataSourcesGrid } from "./DataSourcesGrid";
import type { useGridConfig } from "./DataSourcesGrid.config";

const organizationId = "org-abc";

function getOnAction() {
  return mockUseGridConfig.mock.lastCall![1] as (action: string, item: unknown) => void;
}

describe("DataSourcesGrid", () => {
  const refresh = jest.fn();

  beforeEach(() => {
    mockUseGridConfig.mockReturnValue({
      refresh,
      silentRefresh: jest.fn(),
      onEvent: jest.fn(),
    } as unknown as ReturnType<typeof useGridConfig>);
  });

  it("calls useGridConfig with organizationId and an onAction handler", () => {
    render(<DataSourcesGrid organizationId={organizationId} />);

    expect(mockUseGridConfig).toHaveBeenCalledWith(organizationId, expect.any(Function));
  });

  it("passes the current organizationId to a closed force-import modal", () => {
    render(<DataSourcesGrid organizationId={organizationId} />);

    expect(screen.getByTestId("force-import-modal")).toBeInTheDocument();
    expect(mockForceImportModal).toHaveBeenCalledWith(
      expect.objectContaining({
        isOpen: false,
        datasource: null,
        organizationId,
        className: "force-import-modal",
      }),
    );
  });

  it("opens the force-import modal with the selected item when onAction fires 'force_import'", () => {
    render(<DataSourcesGrid organizationId={organizationId} />);
    const onAction = getOnAction();
    const item = { id: "ds-1", name: "AWS", type: "aws" };

    act(() => {
      onAction("force_import", item);
    });

    expect(mockForceImportModal.mock.lastCall![0]).toMatchObject({
      isOpen: true,
      datasource: item,
      organizationId,
    });
  });

  it("closes the force-import modal when its onClose fires", () => {
    render(<DataSourcesGrid organizationId={organizationId} />);
    const onAction = getOnAction();
    const item = { id: "ds-1", name: "AWS", type: "aws" };
    act(() => onAction("force_import", item));
    expect(mockForceImportModal.mock.lastCall![0].isOpen).toBe(true);

    const onClose = mockForceImportModal.mock.lastCall![0].onClose;
    act(() => onClose());

    expect(mockForceImportModal.mock.lastCall![0].isOpen).toBe(false);
  });

  it("ignores unknown actions", () => {
    render(<DataSourcesGrid organizationId={organizationId} />);
    const onAction = getOnAction();

    act(() => {
      onAction("unsupported_action", { id: "ds-2" });
    });

    expect(mockForceImportModal.mock.lastCall![0].isOpen).toBe(false);
  });
});
