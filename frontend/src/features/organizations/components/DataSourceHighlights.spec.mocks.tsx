import type { useFormatMoney } from "~shared/utils/NumberUtils";
import { mockDesignSystemAvatar } from "~test-utils/mocks/designSystemAvatar";
import { mockDesignSystemNavigation } from "~test-utils/mocks/designSystemNavigation";
import { mockDesignSystemSkeleton } from "~test-utils/mocks/designSystemSkeleton";
import { mockDesignSystemUtils } from "~test-utils/mocks/designSystemUtils";
import { mockEntityReferenceCell } from "~test-utils/mocks/entityReferenceCell";
import { mockDesignSystemInPageHighlight } from "~test-utils/mocks/inPageHighlight";

import type { useDataSourceApi } from "../api/useDataSourceApi";
import type { useOrganizationDetailsApi } from "../api/useOrganizationDetailsApi";

export const mockUseOrganizationDetailsApi = jest.fn() as jest.MockedFunction<
  typeof useOrganizationDetailsApi
>;
export const mockUseDataSourceApi = jest.fn() as jest.MockedFunction<typeof useDataSourceApi>;
export const mockUseFormatMoney = jest.fn() as jest.MockedFunction<typeof useFormatMoney>;

jest.mock("../api/useOrganizationDetailsApi", () => ({
  useOrganizationDetailsApi: (id: string | undefined) => mockUseOrganizationDetailsApi(id),
}));

jest.mock("../api/useDataSourceApi", () => ({
  useDataSourceApi: (...args: Parameters<typeof useDataSourceApi>) => mockUseDataSourceApi(...args),
}));

jest.mock("~shared/utils/NumberUtils", () => ({
  useFormatMoney: (...args: Parameters<typeof useFormatMoney>) => mockUseFormatMoney(...args),
}));

jest.mock("@swo/design-system/utils", () => mockDesignSystemUtils);
jest.mock("@swo/design-system/navigation", () => mockDesignSystemNavigation);
jest.mock("@swo/design-system/in-page-highlight", () => mockDesignSystemInPageHighlight);
jest.mock("@swo/design-system/skeleton", () => mockDesignSystemSkeleton);
jest.mock("@swo/design-system/entity-reference-cell", () => mockEntityReferenceCell);
jest.mock("@swo/design-system/avatar", () => mockDesignSystemAvatar);
