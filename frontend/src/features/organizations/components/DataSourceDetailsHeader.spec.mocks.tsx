import type { ComponentProps } from "react";

import type { PageShell } from "~shared/components/page-shell";
import { mockDataSourceForceImportModalModule } from "~test-utils/mocks/dataSourceForceImportModal";
import { mockDesignSystemButton } from "~test-utils/mocks/designSystemButton";

import type { useDataSourceApi } from "../api/useDataSourceApi";

export { mockForceImportModal } from "~test-utils/mocks/dataSourceForceImportModal";

type MockPageShellHeaderProps = ComponentProps<typeof PageShell.Header>;

export const mockUseDataSourceApi = jest.fn() as jest.MockedFunction<typeof useDataSourceApi>;
export const mockPageShellHeader = jest.fn() as jest.MockedFunction<
  (props: MockPageShellHeaderProps) => void
>;

jest.mock("../api/useDataSourceApi", () => ({
  useDataSourceApi: (...args: Parameters<typeof useDataSourceApi>) => mockUseDataSourceApi(...args),
}));

jest.mock("~shared/components/page-shell", () => ({
  PageShell: {
    Header: (props: MockPageShellHeaderProps) => {
      mockPageShellHeader(props);
      return (
        <div data-testid="page-shell-header">
          {"title" in props ? props.title : null}
          {props.actions}
        </div>
      );
    },
  },
}));

jest.mock("@swo/design-system/button", () => mockDesignSystemButton);

jest.mock(
  "../details/data-sources/force-import-modal/DataSourceForceImportModal",
  () => mockDataSourceForceImportModalModule,
);
