import { ReactNode } from "react";

import { mockEntityReferenceCell } from "~test-utils/mocks/entityReferenceCell";
import { mockCustomIcon } from "~test-utils/mocks/sharedGridCells";

export const mockModal = jest.fn();
export const mockDatePicker = jest.fn();
export const mockInlineErrorNotification = jest.fn();
export const mockUseForceImportController = jest.fn();

jest.mock("@swo/design-system/entity-reference-cell", () => mockEntityReferenceCell);
jest.mock("~shared/components/custom-icons/CustomIcon", () => mockCustomIcon);

jest.mock("~shared/components/modal/Modal", () => ({
  Modal: (props: { children: ReactNode } & Record<string, unknown>) => {
    mockModal(props);
    return <div data-testid="modal">{props.children}</div>;
  },
}));

jest.mock("@swo/design-system/date-picker", () => ({
  DatePicker: (props: Record<string, unknown>) => {
    mockDatePicker(props);
    return <div data-testid="date-picker" />;
  },
}));

jest.mock("@swo/design-system/in-page-highlight", () => {
  const InPageHighlight = ({ children }: { children: ReactNode }) => <div>{children}</div>;
  InPageHighlight.Item = ({ children, title }: { children: ReactNode; title: ReactNode }) => (
    <div>
      <span data-testid="highlight-title">{title}</span>
      <span data-testid="highlight-value">{children}</span>
    </div>
  );
  return { InPageHighlight };
});

jest.mock("@swo/design-system/notification", () => ({
  InlineNotification: ({ children }: { children: ReactNode }) => (
    <div data-testid="inline-notification">{children}</div>
  ),
}));

jest.mock("@swo/design-system/text", () => ({
  BoldText: ({ children }: { children: ReactNode }) => <>{children}</>,
  RegularText: ({ children }: { children: ReactNode }) => <>{children}</>,
}));

jest.mock("~shared/components/error/InlineErrorNotification", () => ({
  InlineErrorNotification: (props: { error: unknown }) => {
    mockInlineErrorNotification(props);
    return <div data-testid="inline-error" />;
  },
}));

jest.mock("../hooks/useForceImportController", () => ({
  useForceImportController: (...args: unknown[]) => mockUseForceImportController(...args),
}));
