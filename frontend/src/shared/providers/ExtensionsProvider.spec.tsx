import type { PropsWithChildren } from "react";

import { useQueryClient } from "@tanstack/react-query";
import { act, render, screen } from "@testing-library/react";
import type { i18n as I18nInstance } from "i18next";

import { ExtensionsProvider } from "./ExtensionsProvider";

type DesignSystemOptionsValue = {
  languageCode: string;
  dateFormat: string;
  timeFormat: string;
  timeZone: string;
  firstDayOfWeek: number;
};

type DesignSystemOptionsProviderProps = PropsWithChildren<{
  value: DesignSystemOptionsValue;
}>;

type StatusChipLocalisationProviderProps = PropsWithChildren<{
  languageCode: string;
}>;

type I18nextProviderProps = PropsWithChildren<{
  i18n: I18nInstance;
}>;

const mockBrowserRouter = jest.fn() as jest.MockedFunction<(props: PropsWithChildren) => void>;
const mockI18nextProvider = jest.fn() as jest.MockedFunction<(props: I18nextProviderProps) => void>;
const mockDesignSystemOptionsProvider = jest.fn() as jest.MockedFunction<
  (props: DesignSystemOptionsProviderProps) => void
>;
const mockStatusChipLocalisationProvider = jest.fn() as jest.MockedFunction<
  (props: StatusChipLocalisationProviderProps) => void
>;
const mockUserProvider = jest.fn() as jest.MockedFunction<(props: PropsWithChildren) => void>;
const mockErrorHandlerProvider = jest.fn() as jest.MockedFunction<
  (props: PropsWithChildren) => void
>;
const mockMPTContextProvider = jest.fn() as jest.MockedFunction<(props: PropsWithChildren) => void>;

jest.mock("react-router-dom", () => ({
  BrowserRouter: ({ children }: PropsWithChildren) => {
    mockBrowserRouter({ children });
    return <>{children}</>;
  },
}));

jest.mock("react-i18next", () => ({
  I18nextProvider: ({ children, i18n }: I18nextProviderProps) => {
    mockI18nextProvider({ children, i18n });
    return <>{children}</>;
  },
}));

jest.mock("@swo/design-system/utils", () => ({
  DesignSystemOptionsProvider: ({ children, value }: DesignSystemOptionsProviderProps) => {
    mockDesignSystemOptionsProvider({ children, value });
    return <>{children}</>;
  },
}));

jest.mock("@swo/mp-status-chip/context", () => ({
  StatusChipLocalisationProvider: ({
    children,
    languageCode,
  }: StatusChipLocalisationProviderProps) => {
    mockStatusChipLocalisationProvider({ children, languageCode });
    return <>{children}</>;
  },
}));

jest.mock("./UserProvider", () => ({
  UserProvider: ({ children }: PropsWithChildren) => {
    mockUserProvider({ children });
    return <>{children}</>;
  },
}));

jest.mock("./ErrorHandlerProvider", () => ({
  ErrorHandlerProvider: ({ children }: PropsWithChildren) => {
    mockErrorHandlerProvider({ children });
    return <>{children}</>;
  },
}));

jest.mock("~shared/providers/MPTContextProvider", () => ({
  MPTContextProvider: ({ children }: PropsWithChildren) => {
    mockMPTContextProvider({ children });
    return <>{children}</>;
  },
}));

function createDeferred() {
  let resolvePromise: () => void = () => undefined;
  const promise = new Promise<void>((resolve) => {
    resolvePromise = resolve;
  });

  return { promise, resolvePromise };
}

function QueryClientConsumer() {
  const queryClient = useQueryClient();

  return <div data-testid="query-options">{JSON.stringify(queryClient.getDefaultOptions())}</div>;
}

describe("ExtensionsProvider", () => {
  it("waits for the language change before rendering the provider tree", async () => {
    const deferred = createDeferred();
    const changeLanguage = jest.fn().mockReturnValue(deferred.promise);
    const i18n = { changeLanguage } as unknown as I18nInstance;

    render(
      <ExtensionsProvider i18n={i18n}>
        <div data-testid="child">child</div>
        <QueryClientConsumer />
      </ExtensionsProvider>,
    );

    expect(screen.queryByTestId("child")).not.toBeInTheDocument();
    expect(mockUserProvider).not.toHaveBeenCalled();
    expect(changeLanguage).toHaveBeenCalledWith("en-US");

    await act(async () => {
      deferred.resolvePromise();
      await deferred.promise;
    });

    expect(await screen.findByTestId("child")).toBeInTheDocument();
    expect(mockUserProvider).toHaveBeenCalledTimes(1);
    expect(mockErrorHandlerProvider).toHaveBeenCalledTimes(1);
    expect(mockMPTContextProvider).toHaveBeenCalledTimes(1);
    expect(mockBrowserRouter).toHaveBeenCalledTimes(1);
    expect(mockI18nextProvider.mock.lastCall?.[0].i18n).toBe(i18n);
    expect(mockDesignSystemOptionsProvider.mock.lastCall?.[0].value).toEqual({
      languageCode: "en-US",
      dateFormat: "d MMM yyyy",
      timeFormat: "HH:mm:ss",
      timeZone: "UTC",
      firstDayOfWeek: 0,
    });
    expect(mockStatusChipLocalisationProvider.mock.lastCall?.[0].languageCode).toBe("en-US");
    expect(screen.getByTestId("query-options")).toHaveTextContent('"staleTime":60000');
    expect(screen.getByTestId("query-options")).toHaveTextContent('"retry":false');
    expect(screen.getByTestId("query-options")).toHaveTextContent('"refetchOnWindowFocus":false');
    expect(screen.getByTestId("query-options")).toHaveTextContent('"refetchOnReconnect":false');
  });
});
