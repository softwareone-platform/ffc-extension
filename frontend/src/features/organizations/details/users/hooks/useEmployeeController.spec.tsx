import { act, renderHook, waitFor } from "@testing-library/react";
import type { AxiosError } from "axios";

import type { useEmployeesApi } from "~features/organizations/api/useEmployeesApi";
import type { useErrorDetails } from "~shared/hooks/useErrorDetails";
import { createQueryClientWrapper, makeEmployee } from "~test-utils";

import { useEmployeeController } from "./useEmployeeController";

type EmployeesApi = ReturnType<typeof useEmployeesApi>;
type ErrorDetails = ReturnType<typeof useErrorDetails>;
type PromoteResult = Awaited<ReturnType<EmployeesApi["promoteToAdmin"]>>;
const OK_RESPONSE = undefined as unknown as PromoteResult;

const mockPromoteToAdmin = jest.fn() as jest.MockedFunction<EmployeesApi["promoteToAdmin"]>;
const mockGetErrorMessage = jest.fn() as jest.MockedFunction<ErrorDetails["getErrorMessage"]>;

jest.mock("~features/organizations/api/useEmployeesApi", () => ({
  useEmployeesApi: () => ({ promoteToAdmin: mockPromoteToAdmin }),
}));

jest.mock("~shared/hooks/useErrorDetails", () => ({
  useErrorDetails: () => ({ getErrorMessage: mockGetErrorMessage }),
}));

function renderController(onClose?: (result?: { success?: boolean }) => void) {
  return renderHook(() => useEmployeeController({ onClose }), {
    wrapper: createQueryClientWrapper(),
  });
}

describe("useEmployeeController", () => {
  const employee = makeEmployee({ id: "emp-1" });

  it("initializes with no error and isPending=false", () => {
    const { result } = renderController();

    expect(result.current.error).toBeNull();
    expect(result.current.isPending).toBe(false);
  });

  it("makeAdmin calls promoteToAdmin with the organization id and employee id", async () => {
    mockPromoteToAdmin.mockResolvedValueOnce(OK_RESPONSE);
    const { result } = renderController();

    await act(async () => {
      await result.current.makeAdmin({ organizationId: "org-1", employee });
    });

    expect(mockPromoteToAdmin).toHaveBeenCalledWith("org-1", "emp-1");
  });

  it("calls onClose with success after a successful mutation", async () => {
    mockPromoteToAdmin.mockResolvedValueOnce(OK_RESPONSE);
    const onClose = jest.fn();
    const { result } = renderController(onClose);

    await act(async () => {
      await result.current.makeAdmin({ organizationId: "org-1", employee });
    });

    await waitFor(() => expect(onClose).toHaveBeenCalledWith({ success: true }));
  });

  it("sets error to getErrorMessage output when the mutation rejects", async () => {
    const failure = new Error("boom") as AxiosError;
    mockGetErrorMessage.mockReturnValue("readable failure");
    mockPromoteToAdmin.mockRejectedValueOnce(failure);
    const { result } = renderController();

    await act(async () => {
      await result.current.makeAdmin({ organizationId: "org-1", employee }).catch(() => undefined);
    });

    await waitFor(() => expect(result.current.error).toBe("readable failure"));
    expect(mockGetErrorMessage).toHaveBeenCalledWith(failure);
  });

  it("cancel calls onClose without arguments when provided", () => {
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
