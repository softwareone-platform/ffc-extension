import { useCallback } from "react";

import { AxiosError } from "axios";

import { useFixedT } from "./useFixedT";

export type ErrorData = {
  detail?: string | unknown[];
};

export function useErrorDetails(namespace: string) {
  const tErrors = useFixedT(namespace);

  const getErrorMessage = useCallback(
    (error: AxiosError) => {
      const errorCodeMessage = tErrors("failed_with_code", {
        code: error.response?.status || "unknown",
      });

      if (!error.response?.data || typeof error.response?.data !== "object") {
        return errorCodeMessage;
      }

      const data: ErrorData = error.response?.data;
      const errorDetails = typeof data?.detail === "string" ? "\n" + data.detail : "";

      return errorCodeMessage + errorDetails;
    },
    [tErrors],
  );
  return { getErrorMessage };
}
