import { act, render, screen } from "@testing-library/react";

import { makeDatasource } from "~test-utils";

import {
  mockDatePicker,
  mockInlineErrorNotification,
  mockModal,
  mockUseForceImportController,
} from "./DataSourceForceImportModal.spec.mocks";

import type { useForceImportController } from "../hooks/useForceImportController";
import { DataSourceForceImportModal } from "./DataSourceForceImportModal";

type Controller = ReturnType<typeof useForceImportController>;

type ModalProps = React.ComponentProps<typeof DataSourceForceImportModal>;

function primeController(overrides: Partial<Controller> = {}): Controller {
  const controller: Controller = {
    cancel: jest.fn(),
    forceImport: jest.fn(),
    isPending: false,
    error: null,
    reset: jest.fn(),
    lastImportAt: undefined,
    setLastImportAt: jest.fn(),
    ...overrides,
  };
  mockUseForceImportController.mockReturnValue(controller);
  return controller;
}

function makeProps(overrides: Partial<ModalProps> = {}): ModalProps {
  return {
    isOpen: true,
    onClose: jest.fn(),
    datasource: makeDatasource(),
    organizationId: "org-123",
    ...overrides,
  };
}

function renderModal(overrides: Partial<ModalProps> = {}) {
  return render(<DataSourceForceImportModal {...makeProps(overrides)} />);
}

describe("DataSourceForceImportModal", () => {
  const organizationId = "org-123";
  const datasource = makeDatasource();

  describe("reset effect", () => {
    it("does not call reset while the modal is closed", () => {
      const controller = primeController();

      renderModal({ isOpen: false, datasource, organizationId });

      expect(controller.reset).not.toHaveBeenCalled();
    });

    it("calls reset when the modal opens", () => {
      const controller = primeController();

      renderModal({ datasource, organizationId });

      expect(controller.reset).toHaveBeenCalledTimes(1);
    });

    it("calls reset again the next time the modal reopens", () => {
      const controller = primeController();
      const { rerender } = renderModal({ datasource, organizationId });
      rerender(
        <DataSourceForceImportModal
          {...makeProps({ isOpen: false, datasource, organizationId })}
        />,
      );
      rerender(<DataSourceForceImportModal {...makeProps({ datasource, organizationId })} />);

      expect(controller.reset).toHaveBeenCalledTimes(2);
    });
  });

  describe("submit", () => {
    it("invokes forceImport with organizationId and datasource when the modal submits with a datasource", () => {
      const controller = primeController();
      renderModal({ datasource, organizationId });

      act(() => mockModal.mock.lastCall![0].onSubmit());

      expect(controller.forceImport).toHaveBeenCalledWith({ organizationId, datasource });
    });

    it("does nothing on submit when the datasource is null", () => {
      const controller = primeController();
      renderModal({ datasource: null, organizationId });

      act(() => mockModal.mock.lastCall![0].onSubmit());

      expect(controller.forceImport).not.toHaveBeenCalled();
    });
  });

  it.each([
    { scenario: "null datasource", input: null, primary: "", secondary: "", icon: "unknown" },
    {
      scenario: "populated datasource",
      input: datasource,
      primary: "AWS Prod",
      secondary: "aws-prod-123",
      icon: "aws_cnr",
    },
  ])("renders EntityReferenceCell for $scenario", ({ input, primary, secondary, icon }) => {
    primeController();
    renderModal({ datasource: input, organizationId });

    expect(screen.getByTestId("primary")).toHaveTextContent(primary);
    expect(screen.getByTestId("secondary")).toHaveTextContent(secondary);
    expect(screen.getByTestId("custom-icon")).toHaveTextContent(icon);
  });

  describe("Modal / DatePicker wiring", () => {
    it("forwards controller state to Modal and DatePicker", () => {
      const lastImportAt = new Date("2026-01-15T00:00:00Z");
      primeController({ isPending: true, lastImportAt });
      renderModal({ datasource, organizationId, className: "force-import-modal" });

      const modalProps = mockModal.mock.lastCall![0];
      const datePickerProps = mockDatePicker.mock.lastCall![0];
      expect(modalProps).toMatchObject({
        isOpen: true,
        className: "force-import-modal",
        testId: "force-import-modal",
        isSubmitting: true,
      });
      expect(datePickerProps).toMatchObject({
        value: lastImportAt,
        isDisabled: true,
      });
    });

    it("wires Modal onCancel to controller.cancel and DatePicker onChange to controller.setLastImportAt", () => {
      const controller = primeController();
      renderModal({ datasource, organizationId });

      mockModal.mock.lastCall![0].onCancel();
      const picked = new Date("2026-02-01T00:00:00Z");
      mockDatePicker.mock.lastCall![0].onChange(picked);

      expect(controller.cancel).toHaveBeenCalledTimes(1);
      expect(controller.setLastImportAt).toHaveBeenCalledWith(picked);
    });
  });

  describe("error surface", () => {
    it("forwards the controller's error to InlineErrorNotification", () => {
      primeController({ error: "boom" });
      renderModal({ datasource, organizationId });

      expect(mockInlineErrorNotification).toHaveBeenLastCalledWith({ error: "boom" });
    });
  });

  it("passes onClose from props to the controller", () => {
    const onClose = jest.fn();
    primeController();

    renderModal({ onClose, datasource, organizationId });

    expect(mockUseForceImportController).toHaveBeenLastCalledWith({ onClose });
  });
});
