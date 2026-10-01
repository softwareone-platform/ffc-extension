import { useQueryClient } from "@tanstack/react-query";
import { act, render, screen } from "@testing-library/react";
import type { i18n as I18nInstance } from "i18next";

import {
  mockBrowserRouter,
  mockDesignSystemOptionsProvider,
  mockErrorHandlerProvider,
  mockI18nextProvider,
  mockMPTContextProvider,
  mockStatusChipLocalisationProvider,
  mockUserProvider,
} from "./ExtensionsProvider.spec.mocks";

import { ExtensionsProvider } from "./ExtensionsProvider";

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
