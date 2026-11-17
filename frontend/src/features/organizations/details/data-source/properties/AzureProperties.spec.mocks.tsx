import { mockCustomIcon } from "~test-utils/mocks/customIcon";
import { mockDesignSystemText } from "~test-utils/mocks/designSystemText";
import { mockDesignSystemUtils } from "~test-utils/mocks/designSystemUtils";
import { mockEntityReferenceCell } from "~test-utils/mocks/entityReferenceCell";
import { mockFormatDateModule } from "~test-utils/mocks/formatDate";
import { mockDesignSystemInPageHighlight } from "~test-utils/mocks/inPageHighlight";
import { mockReactRouterLink } from "~test-utils/mocks/reactRouterLink";

jest.mock("@swo/design-system/in-page-highlight", () => mockDesignSystemInPageHighlight);
jest.mock("@swo/design-system/text", () => mockDesignSystemText);
jest.mock("@swo/design-system/utils", () => mockDesignSystemUtils);
jest.mock("@swo/design-system/entity-reference-cell", () => mockEntityReferenceCell);
jest.mock("~shared/components/custom-icons/CustomIcon", () => mockCustomIcon);
jest.mock("~shared/hooks/useFormatDate", () => mockFormatDateModule);
jest.mock("react-router-dom", () => mockReactRouterLink);
