import type { useErrorDetails } from "~shared/hooks/useErrorDetails";

type ErrorDetails = ReturnType<typeof useErrorDetails>;

export const mockGetErrorMessage = jest.fn() as jest.MockedFunction<
  ErrorDetails["getErrorMessage"]
>;

export const mockErrorDetailsModule = {
  useErrorDetails: () => ({ getErrorMessage: mockGetErrorMessage }),
};
