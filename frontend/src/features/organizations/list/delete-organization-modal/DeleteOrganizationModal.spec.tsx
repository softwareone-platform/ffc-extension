import type { ComponentProps } from "react";

import { render, screen } from "@testing-library/react";

import { makeOrganization, triggerModalCancel, triggerModalSubmit } from "~test-utils";
import { mockDesignSystemUtils } from "~test-utils/mocks/designSystemUtils";
import {
  mockInlineErrorNotification,
  mockSharedInlineErrorNotification,
} from "~test-utils/mocks/inlineErrorNotification";
import { mockModal, mockSharedModal } from "~test-utils/mocks/modal";

import { DeleteOrganizationModal } from "./DeleteOrganizationModal";
import type { useDeleteOrganizationController } from "./hooks/useDeleteOrganizationController";

type Controller = ReturnType<typeof useDeleteOrganizationController>;
type MockInlineNotificationProps = ComponentProps<
  typeof import("@swo/design-system/notification").InlineNotification
>;

const mockUseDeleteController = jest.fn() as jest.MockedFunction<
  typeof useDeleteOrganizationController
>;
const mockFormatDate = jest.fn((v: unknown) => `date(${String(v)})`);
const mockUseFormatDate = jest.fn(() => mockFormatDate);

jest.mock("~shared/components/modal/Modal", () => mockSharedModal);

jest.mock(
  "~shared/components/error/InlineErrorNotification",
  () => mockSharedInlineErrorNotification,
);

jest.mock("@swo/design-system/notification", () => ({
  InlineNotification: ({ children }: MockInlineNotificationProps) => (
    <div data-testid="not-deletable-warning">{children}</div>
  ),
}));

jest.mock("@swo/design-system/utils", () => ({
  ...mockDesignSystemUtils,
  useFormatDate: () => mockUseFormatDate(),
}));

jest.mock("./hooks/useDeleteOrganizationController", () => ({
  useDeleteOrganizationController: (...args: Parameters<typeof useDeleteOrganizationController>) =>
    mockUseDeleteController(...args),
}));

function primeController(overrides: Partial<Controller> = {}): Controller {
  const controller: Controller = {
    handleCancel: jest.fn(),
    remove: jest.fn().mockResolvedValue(undefined),
    isPending: false,
    error: null,
    ...overrides,
  };
  mockUseDeleteController.mockReturnValue(controller);
  return controller;
}

describe("DeleteOrganizationModal", () => {
  it("passes onClose into the controller", () => {
    primeController();
    const onClose = jest.fn();

    render(<DeleteOrganizationModal isOpen onClose={onClose} organization={makeOrganization()} />);

    expect(mockUseDeleteController).toHaveBeenCalledWith({ onClose });
  });

  it("forwards controller.error to InlineErrorNotification", () => {
    primeController({ error: "boom" });

    render(
      <DeleteOrganizationModal isOpen onClose={jest.fn()} organization={makeOrganization()} />,
    );

    expect(mockInlineErrorNotification).toHaveBeenLastCalledWith({ error: "boom" });
  });

  it("disables submit and shows the warning when deletable_at is in the future", () => {
    primeController();
    const future = new Date(Date.now() + 60_000).toISOString();

    render(
      <DeleteOrganizationModal
        isOpen
        onClose={jest.fn()}
        organization={makeOrganization({ deletable_at: future })}
      />,
    );

    expect(mockModal.mock.lastCall![0]).toMatchObject({ isSubmitDisabled: true });
    expect(screen.getByTestId("not-deletable-warning")).toBeInTheDocument();
  });

  it("enables submit and hides the warning when deletable_at is in the past", () => {
    primeController();
    const past = new Date(Date.now() - 60_000).toISOString();

    render(
      <DeleteOrganizationModal
        isOpen
        onClose={jest.fn()}
        organization={makeOrganization({ deletable_at: past })}
      />,
    );

    expect(mockModal.mock.lastCall![0]).toMatchObject({ isSubmitDisabled: false });
    expect(screen.queryByTestId("not-deletable-warning")).not.toBeInTheDocument();
  });

  it("treats an organization without deletable_at as not deletable", () => {
    primeController();

    render(
      <DeleteOrganizationModal
        isOpen
        onClose={jest.fn()}
        organization={makeOrganization({ deletable_at: undefined })}
      />,
    );

    expect(mockModal.mock.lastCall![0]).toMatchObject({ isSubmitDisabled: true });
  });

  it("submit invokes controller.remove with the organization then onSuccess", async () => {
    const remove = jest.fn().mockResolvedValue(undefined);
    primeController({ remove });
    const onSuccess = jest.fn();
    const past = new Date(Date.now() - 60_000).toISOString();
    const organization = makeOrganization({ deletable_at: past });

    render(
      <DeleteOrganizationModal
        isOpen
        onClose={jest.fn()}
        organization={organization}
        onSuccess={onSuccess}
      />,
    );
    await triggerModalSubmit(mockModal);

    expect(remove).toHaveBeenCalledWith(organization);
    expect(onSuccess).toHaveBeenCalledTimes(1);
  });

  it("submit is a noop when the organization is null", async () => {
    const remove = jest.fn();
    primeController({ remove });

    render(<DeleteOrganizationModal isOpen onClose={jest.fn()} organization={null} />);
    await triggerModalSubmit(mockModal);

    expect(remove).not.toHaveBeenCalled();
  });

  it("wires Modal onCancel to controller.handleCancel", () => {
    const controller = primeController();

    render(
      <DeleteOrganizationModal isOpen onClose={jest.fn()} organization={makeOrganization()} />,
    );
    triggerModalCancel(mockModal);

    expect(controller.handleCancel).toHaveBeenCalledTimes(1);
  });
});
