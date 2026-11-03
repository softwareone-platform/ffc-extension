import type { ComponentProps } from "react";

import type { Link } from "react-router-dom";

import { mockDesignSystemAvatar } from "~test-utils/mocks/designSystemAvatar";
import { mockDesignSystemGrid } from "~test-utils/mocks/designSystemGrid";
import { mockEntityReferenceCell } from "~test-utils/mocks/entityReferenceCell";
import { mockEntityStatusChip } from "~test-utils/mocks/entityStatusChip";
import { mockGridCellDynamicActions } from "~test-utils/mocks/gridCellDynamicActions";
import { mockUserRoleModule } from "~test-utils/mocks/userRole";

import type { useActionOptions } from "./useActionOptions";

export { mockStatus } from "~test-utils/mocks/entityStatusChip";
export { mockUseUserRole } from "~test-utils/mocks/userRole";

export const mockGetActions = jest.fn() as jest.MockedFunction<ReturnType<typeof useActionOptions>>;

jest.mock("@swo/design-system/grid", () => mockDesignSystemGrid);
jest.mock("@swo/design-system/entity-reference-cell", () => mockEntityReferenceCell);
jest.mock("@swo/design-system/avatar", () => mockDesignSystemAvatar);

jest.mock("~shared/components/entity-status-chip/EntityStatusChip", () => mockEntityStatusChip);

jest.mock("~shared/components/grid/GridCellDynamicActions", () => mockGridCellDynamicActions);
jest.mock("~shared/hooks/useUserRole", () => mockUserRoleModule);

jest.mock("react-router-dom", () => {
  const actual = jest.requireActual("react-router-dom");
  return { ...actual, Link: ({ children }: ComponentProps<typeof Link>) => <>{children}</> };
});

jest.mock("./useActionOptions", () => ({
  useActionOptions: () => mockGetActions,
}));
