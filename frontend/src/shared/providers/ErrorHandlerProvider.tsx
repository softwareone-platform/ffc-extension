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

import { ErrorPage } from "~shared/components/error/ErrorPage";

import { ErrorBoundary } from "./ErrorBoundary";

export type ErrorCode = "403" | "404" | "500" | "Forbidden" | "NotFound" | "InternalServerError";

export function useErrorHandler() {
  return useContext(ErrorHandlerContext);
}

export const ErrorHandlerContext = createContext<{
  handleError: (errorCode: ErrorCode, data?: ReactNode, useDefaultDescription?: boolean) => void;
}>({
  handleError: () => {},
});

export function ErrorHandlerProvider({ children }: PropsWithChildren) {
  const [error, setError] = useState<ErrorCode | null>(null);
  const [errorDescription, setErrorDescription] = useState<ReactNode | null>(null);

  useEffect(() => {
    const onPopstate = () => {
      setError(null);
      setErrorDescription(null);
    };

    window.addEventListener("popstate", onPopstate);

    return () => window.removeEventListener("popstate", onPopstate);
  }, []);

  const handleError = useCallback(
    (errorCode: ErrorCode, data?: ReactNode, useDefaultDescription?: boolean) => {
      console.log(
        `ErrorHandlerProvider: handleError called with errorCode=${errorCode}, data=${data}, useDefaultDescription=${useDefaultDescription}`,
      );
      setError(errorCode);
      setErrorDescription(data);
    },
    [],
  );

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
          <ErrorPage title={error} errorDescription={errorDescription} />
        </Suspense>
      );
  }

  return (
    <ErrorHandlerContext.Provider value={value}>
      <ErrorBoundary
        fallback={
          <Suspense>
            <ErrorPage
              title="500 Internal Server Error"
              errorDescription="An unexpected error occurred."
            />
          </Suspense>
        }
      >
        {children}
      </ErrorBoundary>
    </ErrorHandlerContext.Provider>
  );
}
