import { act, render, renderHook, screen } from "@testing-library/react";

import {
  MPTContextProvider,
  useHasMPTHost,
  useIsRootPage,
  useMPT,
  useMPTAuth,
  useMPTData,
} from "./MPTContextProvider";

const mockUseMPTContext = jest.fn();

jest.mock(
  "@mpt-extension/sdk-react",
  () => ({
    useMPTContext: () => mockUseMPTContext(),
  }),
  { virtual: true },
);

function ContextConsumer() {
  const context = useMPT();
  const auth = useMPTAuth();
  const data = useMPTData();
  const isRootPage = useIsRootPage();

  return (
    <>
      <div data-testid="context">{JSON.stringify(context)}</div>
      <div data-testid="user-id">{auth?.user.id ?? "missing"}</div>
      <div data-testid="sample">{data?.sample ?? "missing"}</div>
      <div data-testid="root-page">{String(isRootPage)}</div>
    </>
  );
}

describe("MPTContextProvider", () => {
  beforeEach(() => {
    globalThis.__MPT__ = undefined;
    jest.useRealTimers();
  });

  afterEach(() => {
    globalThis.__MPT__ = undefined;
    jest.useRealTimers();
  });

  it("provides empty context values when the host is unavailable", () => {
    render(
      <MPTContextProvider>
        <ContextConsumer />
      </MPTContextProvider>,
    );

    expect(screen.getByTestId("context")).toHaveTextContent("{}");
    expect(screen.getByTestId("user-id")).toHaveTextContent("missing");
    expect(screen.getByTestId("sample")).toHaveTextContent("missing");
    expect(screen.getByTestId("root-page")).toHaveTextContent("false");
  });

  it("bridges the host context when the host is available", () => {
    globalThis.__MPT__ = {};
    mockUseMPTContext.mockReturnValue({
      auth: {
        user: { id: "user-1" },
        account: { id: "account-1", type: "admin" },
      },
      data: {
        isRootPage: true,
        sample: "value",
      },
    });

    render(
      <MPTContextProvider>
        <ContextConsumer />
      </MPTContextProvider>,
    );

    expect(screen.getByTestId("context")).toHaveTextContent('"sample":"value"');
    expect(screen.getByTestId("user-id")).toHaveTextContent("user-1");
    expect(screen.getByTestId("sample")).toHaveTextContent("value");
    expect(screen.getByTestId("root-page")).toHaveTextContent("true");
  });

  it("falls back to an empty host context when the host bridge returns undefined", () => {
    globalThis.__MPT__ = {};
    mockUseMPTContext.mockReturnValue(undefined);

    render(
      <MPTContextProvider>
        <ContextConsumer />
      </MPTContextProvider>,
    );

    expect(screen.getByTestId("context")).toHaveTextContent("{}");
    expect(screen.getByTestId("user-id")).toHaveTextContent("missing");
    expect(screen.getByTestId("sample")).toHaveTextContent("missing");
    expect(screen.getByTestId("root-page")).toHaveTextContent("false");
  });

  it("switches from standalone mode to the host bridge when the host appears after mount", () => {
    jest.useFakeTimers();
    mockUseMPTContext.mockReturnValue({
      auth: {
        user: { id: "user-2" },
        account: { id: "account-2", type: "affiliate" },
      },
      data: {
        isRootPage: false,
        sample: "late-value",
      },
    });

    render(
      <MPTContextProvider>
        <ContextConsumer />
      </MPTContextProvider>,
    );

    expect(screen.getByTestId("user-id")).toHaveTextContent("missing");

    act(() => {
      globalThis.__MPT__ = {};
      jest.advanceTimersByTime(50);
    });

    expect(screen.getByTestId("user-id")).toHaveTextContent("user-2");
    expect(screen.getByTestId("sample")).toHaveTextContent("late-value");
    expect(screen.getByTestId("root-page")).toHaveTextContent("false");
  });

  it("updates host availability when the host is injected after mount", () => {
    jest.useFakeTimers();

    const { result } = renderHook(() => useHasMPTHost());

    expect(result.current).toBe(false);

    act(() => {
      globalThis.__MPT__ = {};
      jest.advanceTimersByTime(50);
    });

    expect(result.current).toBe(true);
  });

  it("keeps reporting no host when polling times out without host injection", () => {
    jest.useFakeTimers();

    const { result } = renderHook(() => useHasMPTHost());

    act(() => {
      jest.advanceTimersByTime(5000);
    });

    expect(result.current).toBe(false);
  });
});
