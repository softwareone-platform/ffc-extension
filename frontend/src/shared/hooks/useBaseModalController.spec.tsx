import type { MutationFunction } from "@tanstack/react-query";
import { act, renderHook, waitFor } from "@testing-library/react";
import type { AxiosError } from "axios";

import type { ModalCloseResult } from "~shared/components/modal/types";
import type { useErrorDetails } from "~shared/hooks/useErrorDetails";
import { createQueryClientWrapper } from "~test-utils";
import { mockGetErrorMessage } from "~test-utils/mocks/errorDetails";

import { useBaseModalController } from "./useBaseModalController";

type Variables = { id: string };

const NAMESPACE = "feature:action:errors";
const FAILURE = new Error("boom") as AxiosError;

const mockUseErrorDetails = jest.fn((_namespace: string) => ({
  getErrorMessage: mockGetErrorMessage,
})) as jest.MockedFunction<typeof useErrorDetails>;

jest.mock("~shared/hooks/useErrorDetails", () => ({
  useErrorDetails: (...args: Parameters<typeof useErrorDetails>) => mockUseErrorDetails(...args),
}));

const mockMutationFn = jest.fn() as jest.MockedFunction<MutationFunction<string, Variables>>;

function renderController({
  onClose,
  reset,
}: {
  onClose?: (result?: ModalCloseResult) => void;
  reset?: () => void;
} = {}) {
  return renderHook(
    () =>
      useBaseModalController({ namespace: NAMESPACE, mutationFn: mockMutationFn, onClose, reset }),
    { wrapper: createQueryClientWrapper() },
  );
}

describe("useBaseModalController", () => {
  beforeEach(() => {
    mockGetErrorMessage.mockReturnValue("readable failure");
  });

  it("initializes with no error and isPending=false", () => {
    const { result } = renderController();

    expect(result.current.error).toBeNull();
    expect(result.current.isPending).toBe(false);
  });

  it("resolves error messages from the given namespace", () => {
    renderController();

    expect(mockUseErrorDetails).toHaveBeenCalledWith(NAMESPACE);
  });

  it("runs the mutation with the given variables and returns its data", async () => {
    mockMutationFn.mockResolvedValueOnce("done");
    const { result } = renderController();

    let data: string | undefined;
    await act(async () => {
      data = await result.current.mutateAsync({ id: "item-1" });
    });

    expect(mockMutationFn.mock.lastCall![0]).toEqual({ id: "item-1" });
    expect(data).toBe("done");
  });

  it("resets state and closes with success after a successful mutation", async () => {
    mockMutationFn.mockResolvedValueOnce("done");
    const onClose = jest.fn();
    const reset = jest.fn();
    const { result } = renderController({ onClose, reset });

    await act(async () => {
      await result.current.mutateAsync({ id: "item-1" });
    });

    expect(reset).toHaveBeenCalledTimes(1);
    expect(onClose).toHaveBeenCalledWith({ success: true });
  });

  it("clears a previous error after a successful mutation", async () => {
    mockMutationFn.mockRejectedValueOnce(FAILURE).mockResolvedValueOnce("done");
    const { result } = renderController();

    await act(async () => {
      await result.current.mutateAsync({ id: "item-1" }).catch(() => undefined);
    });
    await waitFor(() => expect(result.current.error).toBe("readable failure"));

    await act(async () => {
      await result.current.mutateAsync({ id: "item-1" });
    });

    expect(result.current.error).toBeNull();
  });

  it("sets error to getErrorMessage output and stays open when the mutation rejects", async () => {
    mockMutationFn.mockRejectedValueOnce(FAILURE);
    const onClose = jest.fn();
    const reset = jest.fn();
    const { result } = renderController({ onClose, reset });

    await act(async () => {
      await expect(result.current.mutateAsync({ id: "item-1" })).rejects.toBe(FAILURE);
    });

    await waitFor(() => expect(result.current.error).toBe("readable failure"));
    expect(mockGetErrorMessage).toHaveBeenCalledWith(FAILURE);
    expect(onClose).not.toHaveBeenCalled();
    expect(reset).not.toHaveBeenCalled();
  });

  it("sets error without throwing when mutate rejects", async () => {
    mockMutationFn.mockRejectedValueOnce(FAILURE);
    const { result } = renderController();

    act(() => {
      result.current.mutate({ id: "item-1" });
    });

    await waitFor(() => expect(result.current.error).toBe("readable failure"));
  });

  it("cancel resets state, clears the error and closes without a result", () => {
    const onClose = jest.fn();
    const reset = jest.fn();
    const { result } = renderController({ onClose, reset });

    act(() => {
      result.current.setError("stale error");
    });
    act(() => {
      result.current.cancel();
    });

    expect(reset).toHaveBeenCalledTimes(1);
    expect(result.current.error).toBeNull();
    expect(onClose).toHaveBeenCalledWith();
  });

  it("cancel clears the error when onClose and reset are not provided", () => {
    const { result } = renderController();

    act(() => {
      result.current.setError("stale error");
    });
    act(() => {
      result.current.cancel();
    });

    expect(result.current.error).toBeNull();
  });

  it("closes with success when reset is not provided", async () => {
    mockMutationFn.mockResolvedValueOnce("done");
    const onClose = jest.fn();
    const { result } = renderController({ onClose });

    await act(async () => {
      await result.current.mutateAsync({ id: "item-1" });
    });

    expect(onClose).toHaveBeenCalledWith({ success: true });
  });
});
