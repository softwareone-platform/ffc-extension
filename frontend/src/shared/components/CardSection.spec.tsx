import { render, screen } from "@testing-library/react";

import { mockDesignSystemText } from "~test-utils/mocks/designSystemText";

import { CardSection } from "./CardSection";

jest.mock("@swo/design-system/text", () => mockDesignSystemText);

describe("CardSection", () => {
  it("renders the title above its content", () => {
    render(
      <CardSection title="Additional IDs">
        <p>section body</p>
      </CardSection>,
    );

    const title = screen.getByText("Additional IDs");
    const body = screen.getByText("section body");

    expect(title.compareDocumentPosition(body)).toBe(Node.DOCUMENT_POSITION_FOLLOWING);
  });
});
