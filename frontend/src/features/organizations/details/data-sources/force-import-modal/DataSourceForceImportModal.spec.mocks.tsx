import type { ComponentProps } from "react";

import type { DatePicker } from "@swo/design-system/date-picker";

import { mockCustomIcon } from "~test-utils/mocks/customIcon";
import { mockDesignSystemNotification } from "~test-utils/mocks/designSystemNotification";
import { mockDesignSystemText } from "~test-utils/mocks/designSystemText";
import { mockEntityReferenceCell } from "~test-utils/mocks/entityReferenceCell";
import {
  mockInlineErrorNotification,
  mockSharedInlineErrorNotification,
} from "~test-utils/mocks/inlineErrorNotification";
import { mockDesignSystemInPageHighlight } from "~test-utils/mocks/inPageHighlight";
import { mockModal, mockSharedModal } from "~test-utils/mocks/modal";

import type { useForceImportController } from "../hooks/useForceImportController";

type MockDatePickerProps = ComponentProps<typeof DatePicker>;

export { mockModal, mockInlineErrorNotification };

export const mockDatePicker = jest.fn() as jest.MockedFunction<
  (props: MockDatePickerProps) => void
>;
export const mockUseForceImportController = jest.fn() as jest.MockedFunction<
  typeof useForceImportController
>;

jest.mock("@swo/design-system/entity-reference-cell", () => mockEntityReferenceCell);
jest.mock("@swo/design-system/in-page-highlight", () => mockDesignSystemInPageHighlight);
jest.mock("@swo/design-system/notification", () => mockDesignSystemNotification);
jest.mock("@swo/design-system/text", () => mockDesignSystemText);
jest.mock("~shared/components/custom-icons/CustomIcon", () => mockCustomIcon);
jest.mock("~shared/components/modal/Modal", () => mockSharedModal);
jest.mock(
  "~shared/components/error/InlineErrorNotification",
  () => mockSharedInlineErrorNotification,
);

jest.mock("@swo/design-system/date-picker", () => ({
  DatePicker: (props: MockDatePickerProps) => {
    mockDatePicker(props);
    return <div data-testid="date-picker" />;
  },
}));

jest.mock("../hooks/useForceImportController", () => ({
  useForceImportController: (...args: Parameters<typeof useForceImportController>) =>
    mockUseForceImportController(...args),
}));
