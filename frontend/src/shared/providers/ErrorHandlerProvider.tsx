import {
  createContext,
  PropsWithChildren,
  ReactNode,
  Suspense,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";

import { useLocation } from "react-router-dom";

import { ErrorPage } from "~shared/components/error/ErrorPage";
import { useFixedT } from "~shared/hooks/useFixedT";

import { ErrorBoundary } from "./ErrorBoundary";
import { ExtensionsProviderContext } from "./ExtensionsProvider";

export type ErrorCode = "403" | "404" | "500" | "Forbidden" | "NotFound" | "InternalServerError";

export function useErrorHandler() {
  return useContext(ErrorHandlerContext);
}

export const ErrorHandlerContext = createContext<{
  handleError: (errorCode: ErrorCode, data?: ReactNode) => void;
}>({
  handleError: () => {},
});

export function ErrorHandlerProvider({ children }: PropsWithChildren) {
  const { isStandalone } = useContext(ExtensionsProviderContext);
  const [error, setError] = useState<ErrorCode | null>(null);
  const [errorDescription, setErrorDescription] = useState<ReactNode | null>(null);
  const tError = useFixedT("shared:error");
  const location = useLocation();

  useEffect(() => {
    if (isStandalone) {
      setError(null);
      setErrorDescription(null);
    }
  }, [location, isStandalone]);

  const handleError = useCallback((errorCode: ErrorCode, data?: ReactNode) => {
    setError(errorCode);
    setErrorDescription(data);
  }, []);

  const value = useMemo(() => ({ handleError }), [handleError]);

  switch (error) {
    case "403":
    case "Forbidden":
    case "404":
    case "NotFound":
    case "500":
    case "InternalServerError":
      return (
        <Suspense>
          <ErrorPage title={tError(`title:${error}`)} subtitle={errorDescription} />
        </Suspense>
      );
  }

  return (
    <ErrorHandlerContext.Provider value={value}>
      <ErrorBoundary
        fallback={
          <Suspense>
            <ErrorPage
              title={tError("title:500")}
              subtitle={tError("description:internalServerError")}
            />
          </Suspense>
        }
      >
        {children}
      </ErrorBoundary>
    </ErrorHandlerContext.Provider>
  );
}
