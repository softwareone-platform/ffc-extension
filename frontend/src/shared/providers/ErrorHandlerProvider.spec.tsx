import type { ComponentProps, PropsWithChildren, ReactElement } from "react";

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter, Route, Routes, useNavigate } from "react-router-dom";

import type { ErrorPage } from "~shared/components/error/ErrorPage";
import type { UserEvent } from "~test-utils";

import type { ErrorCode } from "./ErrorHandlerProvider";
import { ErrorHandlerProvider, useErrorHandler } from "./ErrorHandlerProvider";

type MockErrorPageProps = ComponentProps<typeof ErrorPage>;

jest.mock("~shared/components/error/ErrorPage", () => ({
  ErrorPage: ({ title, subtitle }: MockErrorPageProps) => (
    <div data-testid="error-page">
      <div data-testid="error-title">{title}</div>
      {subtitle && <div data-testid="error-subtitle">{subtitle}</div>}
    </div>
  ),
}));

function ProviderHarness({ children }: PropsWithChildren) {
  return (
    <MemoryRouter initialEntries={["/start"]}>
      <RouteChangeButton />
      <Routes>
        <Route path="*" element={<ErrorHandlerProvider>{children}</ErrorHandlerProvider>} />
      </Routes>
    </MemoryRouter>
  );
}

function RouteChangeButton() {
  const navigate = useNavigate();

  return <button onClick={() => navigate("/next")}>go next</button>;
}

function ErrorTrigger({ errorCode, description }: { errorCode: ErrorCode; description: string }) {
  const { handleError } = useErrorHandler();

  return <button onClick={() => handleError(errorCode, description)}>show error</button>;
}

function UnwrappedErrorTrigger() {
  const { handleError } = useErrorHandler();

  return (
    <button onClick={() => handleError("404", "unused-description")}>show default handler</button>
  );
}

function ExplodingChild(): ReactElement {
  throw new Error("boom");
}

describe("ErrorHandlerProvider", () => {
  let mockConsoleError: jest.SpiedFunction<typeof console.error>;
  let user: UserEvent;

  beforeEach(() => {
    user = userEvent.setup();
    mockConsoleError = jest.spyOn(console, "error").mockImplementation(() => undefined);
  });

  afterEach(() => {
    mockConsoleError.mockRestore();
  });

  it("renders children when no error has been reported", () => {
    render(
      <ProviderHarness>
        <div data-testid="child">child</div>
      </ProviderHarness>,
    );

    expect(screen.getByTestId("child")).toBeInTheDocument();
    expect(screen.queryByTestId("error-page")).not.toBeInTheDocument();
  });

  it.each<[ErrorCode, string]>([
    ["403", "forbidden-code-description"],
    ["Forbidden", "forbidden-description"],
    ["404", "not-found-code-description"],
    ["NotFound", "not-found-description"],
    ["500", "server-code-description"],
    ["InternalServerError", "server-description"],
  ])(
    "renders the matching error page when handleError is called with %s",
    async (errorCode, description) => {
      render(
        <ProviderHarness>
          <ErrorTrigger errorCode={errorCode} description={description} />
        </ProviderHarness>,
      );

      await user.click(screen.getByRole("button", { name: "show error" }));

      expect(screen.getByTestId("error-title")).toHaveTextContent(`title:${errorCode}`);
      expect(screen.getByTestId("error-subtitle")).toHaveTextContent(description);
    },
  );

  it("clears the displayed error when the route changes", async () => {
    render(
      <ProviderHarness>
        <>
          <ErrorTrigger errorCode="Forbidden" description="forbidden-description" />
          <div data-testid="child">child</div>
        </>
      </ProviderHarness>,
    );

    await user.click(screen.getByRole("button", { name: "show error" }));
    expect(screen.getByTestId("error-page")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "go next" }));

    expect(await screen.findByTestId("child")).toBeInTheDocument();
    expect(screen.queryByTestId("error-page")).not.toBeInTheDocument();
  });

  it("renders the internal server error fallback when a descendant throws", () => {
    render(
      <ProviderHarness>
        <ExplodingChild />
      </ProviderHarness>,
    );

    expect(screen.getByTestId("error-title")).toHaveTextContent("title:500");
    expect(screen.getByTestId("error-subtitle")).toHaveTextContent(
      "description:internalServerError",
    );
  });

  it("returns a default error handler outside the provider that does nothing", async () => {
    render(<UnwrappedErrorTrigger />);

    await user.click(screen.getByRole("button", { name: "show default handler" }));

    expect(screen.getByRole("button", { name: "show default handler" })).toBeInTheDocument();
  });
});
