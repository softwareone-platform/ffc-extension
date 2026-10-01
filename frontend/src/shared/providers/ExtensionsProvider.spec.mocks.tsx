import type { ComponentProps } from "react";

import type { I18nextProvider } from "react-i18next";
import type { BrowserRouter } from "react-router-dom";

import type { DesignSystemOptionsProvider } from "@swo/design-system/utils";
import type { StatusChipLocalisationProvider } from "@swo/mp-status-chip/context";

import type { ErrorHandlerProvider } from "./ErrorHandlerProvider";
import type { MPTContextProvider } from "./MPTContextProvider";
import type { UserProvider } from "./UserProvider";

type MockBrowserRouterProps = ComponentProps<typeof BrowserRouter>;
type MockDesignSystemOptionsProviderProps = ComponentProps<typeof DesignSystemOptionsProvider>;
type MockStatusChipLocalisationProviderProps = ComponentProps<
  typeof StatusChipLocalisationProvider
>;
type MockI18nextProviderProps = ComponentProps<typeof I18nextProvider>;
type MockUserProviderProps = ComponentProps<typeof UserProvider>;
type MockErrorHandlerProviderProps = ComponentProps<typeof ErrorHandlerProvider>;
type MockMPTContextProviderProps = ComponentProps<typeof MPTContextProvider>;

export const mockBrowserRouter = jest.fn() as jest.MockedFunction<
  (props: MockBrowserRouterProps) => void
>;
export const mockI18nextProvider = jest.fn() as jest.MockedFunction<
  (props: MockI18nextProviderProps) => void
>;
export const mockDesignSystemOptionsProvider = jest.fn() as jest.MockedFunction<
  (props: MockDesignSystemOptionsProviderProps) => void
>;
export const mockStatusChipLocalisationProvider = jest.fn() as jest.MockedFunction<
  (props: MockStatusChipLocalisationProviderProps) => void
>;
export const mockUserProvider = jest.fn() as jest.MockedFunction<
  (props: MockUserProviderProps) => void
>;
export const mockErrorHandlerProvider = jest.fn() as jest.MockedFunction<
  (props: MockErrorHandlerProviderProps) => void
>;
export const mockMPTContextProvider = jest.fn() as jest.MockedFunction<
  (props: MockMPTContextProviderProps) => void
>;

jest.mock("react-router-dom", () => ({
  BrowserRouter: ({ children }: MockBrowserRouterProps) => {
    mockBrowserRouter({ children });
    return <>{children}</>;
  },
}));

jest.mock("react-i18next", () => ({
  I18nextProvider: ({ children, i18n }: MockI18nextProviderProps) => {
    mockI18nextProvider({ children, i18n });
    return <>{children}</>;
  },
}));

jest.mock("@swo/design-system/utils", () => ({
  DesignSystemOptionsProvider: ({ children, value }: MockDesignSystemOptionsProviderProps) => {
    mockDesignSystemOptionsProvider({ children, value });
    return <>{children}</>;
  },
}));

jest.mock("@swo/mp-status-chip/context", () => ({
  StatusChipLocalisationProvider: ({
    children,
    languageCode,
  }: MockStatusChipLocalisationProviderProps) => {
    mockStatusChipLocalisationProvider({ children, languageCode });
    return <>{children}</>;
  },
}));

jest.mock("./UserProvider", () => ({
  UserProvider: ({ children }: MockUserProviderProps) => {
    mockUserProvider({ children });
    return <>{children}</>;
  },
}));

jest.mock("./ErrorHandlerProvider", () => ({
  ErrorHandlerProvider: ({ children }: MockErrorHandlerProviderProps) => {
    mockErrorHandlerProvider({ children });
    return <>{children}</>;
  },
}));

jest.mock("~shared/providers/MPTContextProvider", () => ({
  MPTContextProvider: ({ children }: MockMPTContextProviderProps) => {
    mockMPTContextProvider({ children });
    return <>{children}</>;
  },
}));
