import type { useOrganizationDetailsApi } from "~organizations/api";
import type { useFormatMoney } from "~shared/utils/NumberUtils";
import { mockDesignSystemNavigation } from "~test-utils/mocks/designSystemNavigation";
import { mockDesignSystemSkeleton } from "~test-utils/mocks/designSystemSkeleton";
import { mockDesignSystemUtils } from "~test-utils/mocks/designSystemUtils";
import { mockDesignSystemInPageHighlight } from "~test-utils/mocks/inPageHighlight";

export const mockUseOrganizationDetailsApi = jest.fn() as jest.MockedFunction<
  typeof useOrganizationDetailsApi
>;
export const mockUseFormatMoney = jest.fn() as jest.MockedFunction<typeof useFormatMoney>;

jest.mock("~organizations/api", () => ({
  useOrganizationDetailsApi: (id: string | undefined) => mockUseOrganizationDetailsApi(id),
}));

jest.mock("~shared/utils/NumberUtils", () => ({
  useFormatMoney: (...args: Parameters<typeof useFormatMoney>) => mockUseFormatMoney(...args),
}));

jest.mock("@swo/design-system/utils", () => mockDesignSystemUtils);
jest.mock("@swo/design-system/navigation", () => mockDesignSystemNavigation);
jest.mock("@swo/design-system/in-page-highlight", () => mockDesignSystemInPageHighlight);
jest.mock("@swo/design-system/skeleton", () => mockDesignSystemSkeleton);
