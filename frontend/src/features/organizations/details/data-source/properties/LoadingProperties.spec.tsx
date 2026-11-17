import { render, screen } from "@testing-library/react";

import { mockDesignSystemSkeleton } from "~test-utils/mocks/designSystemSkeleton";
import { mockDesignSystemText } from "~test-utils/mocks/designSystemText";

import { LoadingDataSourceProperties } from "./LoadingProperties";

jest.mock("@swo/design-system/skeleton", () => mockDesignSystemSkeleton);
jest.mock("@swo/design-system/text", () => mockDesignSystemText);

describe("LoadingDataSourceProperties", () => {
  it("renders a skeleton under the supplied section title", () => {
    render(<LoadingDataSourceProperties title="Billing import" />);

    expect(screen.getByText("Billing import")).toBeInTheDocument();
    expect(screen.getByTestId("skeleton")).toBeInTheDocument();
  });

  it("falls back to the properties title when none is supplied", () => {
    render(<LoadingDataSourceProperties />);

    expect(screen.getByText("properties")).toBeInTheDocument();
  });
});
