import type { ComponentProps } from "react";

import type { DataSourceForceImportModal } from "~organizations/details/data-sources/force-import-modal/DataSourceForceImportModal";

type MockDataSourceForceImportModalProps = ComponentProps<typeof DataSourceForceImportModal>;

export const mockForceImportModal = jest.fn() as jest.MockedFunction<
  (props: MockDataSourceForceImportModalProps) => void
>;

export const mockDataSourceForceImportModalModule = {
  DataSourceForceImportModal: (props: MockDataSourceForceImportModalProps) => {
    mockForceImportModal(props);
    return (
      <div
        data-testid="force-import-modal"
        data-open={String(props.isOpen)}
        data-datasource-id={props.datasource?.id ?? ""}
        data-organization-id={props.organizationId}
        data-class-name={props.className ?? ""}
      >
        <button onClick={() => props.onClose()} type="button">
          close force import modal
        </button>
        <button onClick={() => props.onClose({ success: true })} type="button">
          complete force import
        </button>
      </div>
    );
  },
};
