import type { ComponentProps } from "react";

import type { DatePicker } from "@swo/design-system/date-picker";
import type { InlineNotification } from "@swo/design-system/notification";
import type { BoldText, RegularText } from "@swo/design-system/text";

import type { InlineErrorNotification } from "~shared/components/error/InlineErrorNotification";
import type { Modal } from "~shared/components/modal/Modal";
import { mockEntityReferenceCell } from "~test-utils/mocks/entityReferenceCell";
import { mockCustomIcon } from "~test-utils/mocks/sharedGridCells";

import type { useForceImportController } from "../hooks/useForceImportController";

type MockInPageHighlightProps = ComponentProps<
  typeof import("@swo/design-system/in-page-highlight").InPageHighlight
>;
type MockInPageHighlightItemProps = ComponentProps<
  typeof import("@swo/design-system/in-page-highlight").InPageHighlight.Item
>;

type MockBoldTextProps = ComponentProps<typeof BoldText>;
type MockRegularTextProps = ComponentProps<typeof RegularText>;

type MockModalProps = ComponentProps<typeof Modal>;
type MockDatePickerProps = ComponentProps<typeof DatePicker>;
type MockInlineNotificationProps = ComponentProps<typeof InlineNotification>;
type MockInlineErrorNotificationProps = ComponentProps<typeof InlineErrorNotification>;

export const mockModal = jest.fn() as jest.MockedFunction<(props: MockModalProps) => void>;
export const mockDatePicker = jest.fn() as jest.MockedFunction<
  (props: MockDatePickerProps) => void
>;
export const mockInlineErrorNotification = jest.fn() as jest.MockedFunction<
  (props: MockInlineErrorNotificationProps) => void
>;
export const mockUseForceImportController = jest.fn() as jest.MockedFunction<
  typeof useForceImportController
>;

jest.mock("@swo/design-system/entity-reference-cell", () => mockEntityReferenceCell);
jest.mock("~shared/components/custom-icons/CustomIcon", () => mockCustomIcon);

jest.mock("~shared/components/modal/Modal", () => ({
  Modal: (props: MockModalProps) => {
    mockModal(props);
    return <div data-testid="modal">{props.children}</div>;
  },
}));

jest.mock("@swo/design-system/date-picker", () => ({
  DatePicker: (props: MockDatePickerProps) => {
    mockDatePicker(props);
    return <div data-testid="date-picker" />;
  },
}));

jest.mock("@swo/design-system/in-page-highlight", () => {
  const InPageHighlight = ({ children }: MockInPageHighlightProps) => <div>{children}</div>;
  InPageHighlight.Item = ({ children, title }: MockInPageHighlightItemProps) => (
    <div>
      <span data-testid="highlight-title">{title}</span>
      <span data-testid="highlight-value">{children}</span>
    </div>
  );
  return { InPageHighlight };
});

jest.mock("@swo/design-system/notification", () => ({
  InlineNotification: ({ children }: MockInlineNotificationProps) => (
    <div data-testid="inline-notification">{children}</div>
  ),
}));

jest.mock("@swo/design-system/text", () => ({
  BoldText: ({ children }: Pick<MockBoldTextProps, "children">) => <>{children}</>,
  RegularText: ({ children }: Pick<MockRegularTextProps, "children">) => <>{children}</>,
}));

jest.mock("~shared/components/error/InlineErrorNotification", () => ({
  InlineErrorNotification: (props: MockInlineErrorNotificationProps) => {
    mockInlineErrorNotification(props);
    return <div data-testid="inline-error" />;
  },
}));

jest.mock("../hooks/useForceImportController", () => ({
  useForceImportController: (...args: Parameters<typeof useForceImportController>) =>
    mockUseForceImportController(...args),
}));
