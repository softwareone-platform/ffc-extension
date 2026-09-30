import { render, screen } from "@testing-library/react";

import { mockDesignSystemText } from "~test-utils/mocks/designSystemText";
import {
  mockInlineErrorNotification,
  mockSharedInlineErrorNotification,
} from "~test-utils/mocks/inlineErrorNotification";

import { WizardStep } from "./WizardStep";

jest.mock("@swo/design-system/text", () => mockDesignSystemText);
jest.mock("../error/InlineErrorNotification", () => mockSharedInlineErrorNotification);

describe("WizardStep", () => {
  let scrollIntoViewMock: jest.Mock;

  beforeEach(() => {
    scrollIntoViewMock = jest.fn();
    Object.defineProperty(Element.prototype, "scrollIntoView", {
      configurable: true,
      value: scrollIntoViewMock,
    });
  });

  it("renders the title heading and children body", () => {
    render(
      <WizardStep title="Summary" className="custom-step" contentClassName="content-class">
        <div data-testid="step-body">body</div>
      </WizardStep>,
    );

    expect(screen.getByText("Summary")).toBeInTheDocument();
    expect(screen.getByTestId("step-body")).toHaveTextContent("body");
  });

  it("does not render an inline error or scroll when no error is provided", () => {
    render(<WizardStep title="Summary">body</WizardStep>);

    expect(screen.queryByTestId("inline-error")).not.toBeInTheDocument();
    expect(mockInlineErrorNotification).not.toHaveBeenCalled();
    expect(scrollIntoViewMock).not.toHaveBeenCalled();
  });

  it("renders the inline error and scrolls it into view when an error is provided", () => {
    render(
      <WizardStep title="Summary" error="Broken step">
        body
      </WizardStep>,
    );

    expect(screen.getByTestId("inline-error")).toBeInTheDocument();
    expect(mockInlineErrorNotification).toHaveBeenCalledWith({ error: "Broken step" });
    expect(scrollIntoViewMock).toHaveBeenCalledTimes(1);
  });
});
