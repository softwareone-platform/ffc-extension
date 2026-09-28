import type { ReactNode } from "react";

import { fireEvent, render, screen } from "@testing-library/react";

import { mockDesignSystemButton } from "~test-utils/mocks/designSystemButton";

import { ErrorPage } from "./ErrorPage";

const mockNavigate = jest.fn();

jest.mock("react-router-dom", () => {
  const actual = jest.requireActual("react-router-dom");
  return {
    ...actual,
    useNavigate: () => mockNavigate,
  };
});

jest.mock("@swo/design-system/card", () => ({
  Card: ({ children }: { children?: ReactNode }) => <div data-testid="card">{children}</div>,
}));

jest.mock("@swo/design-system/icon", () => ({
  Icon: ({ name }: { name: string }) => <div data-testid="icon">{name}</div>,
}));

jest.mock("@swo/design-system/button", () => mockDesignSystemButton);

describe("ErrorPage", () => {
  beforeEach(() => {
    mockNavigate.mockReset();
  });

  it("renders the provided title, subtitle, and error description", () => {
    render(
      <ErrorPage title="Something went wrong" subtitle="Try again" errorDescription="Details" />,
    );

    expect(screen.getByText("Something went wrong")).toBeInTheDocument();
    expect(screen.getByText("Try again")).toBeInTheDocument();
    expect(screen.getByText("Details")).toBeInTheDocument();
    expect(screen.getByTestId("icon")).toHaveTextContent("release_alert");
    expect(
      screen.getByRole("button", { name: "error-handler:errorPageCard:home" }),
    ).toBeInTheDocument();
  });

  it("navigates home when the home action is clicked", () => {
    render(<ErrorPage title="Something went wrong" />);

    fireEvent.click(screen.getByRole("button", { name: "error-handler:errorPageCard:home" }));

    expect(mockNavigate).toHaveBeenCalledWith("/");
  });
});
