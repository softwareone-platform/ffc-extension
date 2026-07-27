/* eslint-disable react-refresh/only-export-components */
import {
  createContext,
  PropsWithChildren,
  ReactNode,
  Suspense,
  useCallback,
  useContext,
  useMemo,
  useState,
} from "react";

import { useLocation } from "react-router-dom";

import { ErrorPage } from "~shared/components/error/ErrorPage";
import { useFixedT } from "~shared/hooks/useFixedT";

import { ErrorBoundary } from "./ErrorBoundary";

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
  const location = useLocation();
  const [error, setError] = useState<ErrorCode | null>(null);
  const [errorDescription, setErrorDescription] = useState<ReactNode | null>(null);
  const [prevLocationKey, setPrevLocationKey] = useState(location.key);
  const tError = useFixedT("shared:error");

  // Clear any displayed error page when the route changes. Adjusting state
  // during render (React's documented pattern) instead of in an effect avoids
  // a cascading re-render.
  if (location.key !== prevLocationKey) {
    setPrevLocationKey(location.key);
    setError(null);
    setErrorDescription(null);
  }

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
