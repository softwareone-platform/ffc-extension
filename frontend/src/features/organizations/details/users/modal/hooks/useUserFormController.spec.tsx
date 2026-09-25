import { act, renderHook, waitFor } from "@testing-library/react";
import type { AxiosError } from "axios";

import type { useEmployeesApi } from "~features/organizations/api/useEmployeesApi";
import type { useErrorDetails } from "~shared/hooks/useErrorDetails";
import { createQueryClientWrapper } from "~test-utils";

import type { AddUserForm } from "../AddUserForm.Schema";
import type { useAddUserForm } from "./useAddUserForm";
import { useUserFormController } from "./useUserFormController";

type EmployeesApi = ReturnType<typeof useEmployeesApi>;
type ErrorDetails = ReturnType<typeof useErrorDetails>;
type AddResult = Awaited<ReturnType<EmployeesApi["addAdmin"]>>;
type FormReturn = ReturnType<typeof useAddUserForm>;
const OK_RESPONSE = undefined as unknown as AddResult;

const mockAddAdmin = jest.fn() as jest.MockedFunction<EmployeesApi["addAdmin"]>;
const mockGetErrorMessage = jest.fn() as jest.MockedFunction<ErrorDetails["getErrorMessage"]>;
const mockReset = jest.fn();
// handleSubmit(cb) returns () => Promise; simulate by immediately invoking cb with a valid payload.
const validPayload: AddUserForm = { email: "user@example.com", display_name: "User" };
const mockHandleSubmit = jest.fn(
  (cb: (data: AddUserForm) => Promise<void> | void) => () => Promise.resolve(cb(validPayload)),
) as unknown as FormReturn["handleSubmit"];

jest.mock("~features/organizations/api/useEmployeesApi", () => ({
  useEmployeesApi: () => ({ addAdmin: mockAddAdmin }),
}));

jest.mock("~shared/hooks/useErrorDetails", () => ({
  useErrorDetails: () => ({ getErrorMessage: mockGetErrorMessage }),
}));

jest.mock("./useAddUserForm", () => ({
  useAddUserForm: () => ({
    handleSubmit: mockHandleSubmit,
    control: {},
    reset: mockReset,
  }),
}));

function renderController(organizationId: string, onClose = jest.fn()) {
  return renderHook(() => useUserFormController({ organizationId, onClose }), {
    wrapper: createQueryClientWrapper(),
  });
}

describe("useUserFormController", () => {
  it("initializes with no error and isPending=false", () => {
    const { result } = renderController("org-1");

    expect(result.current.error).toBeNull();
    expect(result.current.isPending).toBe(false);
  });

  it("submit calls addAdmin with organizationId and form data", async () => {
    mockAddAdmin.mockResolvedValueOnce(OK_RESPONSE);
    const { result } = renderController("org-1");

    await act(async () => {
      await result.current.submit();
    });

    expect(mockAddAdmin).toHaveBeenCalledWith("org-1", validPayload);
  });

  it("resets the form and calls onClose with success after a successful mutation", async () => {
    mockAddAdmin.mockResolvedValueOnce(OK_RESPONSE);
    const onClose = jest.fn();
    const { result } = renderController("org-1", onClose);

    await act(async () => {
      await result.current.submit();
    });

    await waitFor(() => expect(onClose).toHaveBeenCalledWith({ success: true }));
    expect(mockReset).toHaveBeenCalled();
  });

  it("sets error to getErrorMessage output when the mutation rejects", async () => {
    const failure = new Error("boom") as AxiosError;
    mockGetErrorMessage.mockReturnValue("readable failure");
    mockAddAdmin.mockRejectedValueOnce(failure);
    const { result } = renderController("org-1");

    await act(async () => {
      await result.current.submit().catch(() => undefined);
    });

    await waitFor(() => expect(result.current.error).toBe("readable failure"));
    expect(mockGetErrorMessage).toHaveBeenCalledWith(failure);
  });

  it("handleCancel resets the form and calls onClose", () => {
    const onClose = jest.fn();
    const { result } = renderController("org-1", onClose);

    act(() => {
      result.current.handleCancel();
    });

    expect(mockReset).toHaveBeenCalled();
    expect(onClose).toHaveBeenCalledWith();
  });
});
