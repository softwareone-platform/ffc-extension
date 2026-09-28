import { act, renderHook, waitFor } from "@testing-library/react";
import type { AxiosError } from "axios";

import type { useEntitlementsApi } from "~features/entitlements/api/useEntitlementsApi";
import { createQueryClientWrapper, makeEntitlement } from "~test-utils";
import { mockErrorDetailsModule, mockGetErrorMessage } from "~test-utils/mocks/errorDetails";

import { useEntitlementController } from "./useEntitlementsController";

type EntitlementsApi = ReturnType<typeof useEntitlementsApi>;
type TerminateResult = Awaited<ReturnType<EntitlementsApi["terminateEntitlement"]>>;
type DeleteResult = Awaited<ReturnType<EntitlementsApi["deleteEntitlement"]>>;
const OK_TERMINATE = undefined as unknown as TerminateResult;
const OK_DELETE = undefined as unknown as DeleteResult;

const mockTerminate = jest.fn() as jest.MockedFunction<EntitlementsApi["terminateEntitlement"]>;
const mockDelete = jest.fn() as jest.MockedFunction<EntitlementsApi["deleteEntitlement"]>;

jest.mock("~features/entitlements/api/useEntitlementsApi", () => ({
  useEntitlementsApi: () => ({
    terminateEntitlement: mockTerminate,
    deleteEntitlement: mockDelete,
  }),
}));

jest.mock("~shared/hooks/useErrorDetails", () => mockErrorDetailsModule);

function renderController(onClose?: (result?: { success?: boolean }) => void) {
  return renderHook(() => useEntitlementController({ onClose }), {
    wrapper: createQueryClientWrapper(),
  });
}

describe("useEntitlementController", () => {
  const entitlement = makeEntitlement({ id: "ent-1" });

  it("initializes with no error and both pending flags false", () => {
    const { result } = renderController();

    expect(result.current.error).toBeNull();
    expect(result.current.isPendingTerminate).toBe(false);
    expect(result.current.isPendingRemove).toBe(false);
  });

  it("terminate calls terminateEntitlement with the entitlement id", async () => {
    mockTerminate.mockResolvedValueOnce(OK_TERMINATE);
    const { result } = renderController();

    await act(async () => {
      await result.current.terminate(entitlement);
    });

    expect(mockTerminate).toHaveBeenCalledWith("ent-1");
  });

  it("remove calls deleteEntitlement with the entitlement id", async () => {
    mockDelete.mockResolvedValueOnce(OK_DELETE);
    const { result } = renderController();

    await act(async () => {
      await result.current.remove(entitlement);
    });

    expect(mockDelete).toHaveBeenCalledWith("ent-1");
  });

  it("calls onClose with success after a successful terminate", async () => {
    mockTerminate.mockResolvedValueOnce(OK_TERMINATE);
    const onClose = jest.fn();
    const { result } = renderController(onClose);

    await act(async () => {
      await result.current.terminate(entitlement);
    });

    await waitFor(() => expect(onClose).toHaveBeenCalledWith({ success: true }));
  });

  it("calls onClose with success after a successful remove", async () => {
    mockDelete.mockResolvedValueOnce(OK_DELETE);
    const onClose = jest.fn();
    const { result } = renderController(onClose);

    await act(async () => {
      await result.current.remove(entitlement);
    });

    await waitFor(() => expect(onClose).toHaveBeenCalledWith({ success: true }));
  });

  it("sets error to getErrorMessage output when terminate rejects", async () => {
    const failure = new Error("boom") as AxiosError;
    mockGetErrorMessage.mockReturnValue("readable failure");
    mockTerminate.mockRejectedValueOnce(failure);
    const { result } = renderController();

    await act(async () => {
      await expect(result.current.terminate(entitlement)).rejects.toBeDefined();
    });

    await waitFor(() => expect(result.current.error).toBe("readable failure"));
    expect(mockGetErrorMessage).toHaveBeenCalledWith(failure);
  });

  it("sets error to getErrorMessage output when remove rejects", async () => {
    const failure = new Error("boom") as AxiosError;
    mockGetErrorMessage.mockReturnValue("readable failure");
    mockDelete.mockRejectedValueOnce(failure);
    const { result } = renderController();

    await act(async () => {
      await expect(result.current.remove(entitlement)).rejects.toBeDefined();
    });

    await waitFor(() => expect(result.current.error).toBe("readable failure"));
  });

  it("clears a previous error after a successful terminate retry", async () => {
    const failure = new Error("boom") as AxiosError;
    mockGetErrorMessage.mockReturnValue("readable failure");
    mockTerminate.mockRejectedValueOnce(failure);
    const onClose = jest.fn();
    const { result } = renderController(onClose);

    await act(async () => {
      await expect(result.current.terminate(entitlement)).rejects.toBeDefined();
    });
    await waitFor(() => expect(result.current.error).toBe("readable failure"));

    mockTerminate.mockResolvedValueOnce(OK_TERMINATE);
    await act(async () => {
      await result.current.terminate(entitlement);
    });

    await waitFor(() => expect(result.current.error).toBeNull());
  });

  it("cancel clears error and calls onClose without arguments when provided", () => {
    const onClose = jest.fn();
    const { result } = renderController(onClose);

    act(() => {
      result.current.cancel();
    });

    expect(onClose).toHaveBeenCalledWith();
  });

  it("cancel is a noop when onClose is not provided", () => {
    const { result } = renderController();

    expect(() => act(() => result.current.cancel())).not.toThrow();
  });
});
