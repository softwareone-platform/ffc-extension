import { act, renderHook, waitFor } from "@testing-library/react";
import type { AxiosError } from "axios";

import type { useOrganizationsApi } from "~features/organizations/api/useOrganizationsApi";
import { createQueryClientWrapper, makeOrganization } from "~test-utils";
import { mockErrorDetailsModule, mockGetErrorMessage } from "~test-utils/mocks/errorDetails";

import { useDeleteOrganizationController } from "./useDeleteOrganizationController";

type OrganizationsApi = ReturnType<typeof useOrganizationsApi>;
type DeleteResult = Awaited<ReturnType<OrganizationsApi["deleteOrganization"]>>;

const OK_RESPONSE = undefined as unknown as DeleteResult;

const mockDeleteOrganization = jest.fn() as jest.MockedFunction<
  OrganizationsApi["deleteOrganization"]
>;

jest.mock("~features/organizations/api/useOrganizationsApi", () => ({
  useOrganizationsApi: () => ({ deleteOrganization: mockDeleteOrganization }),
}));

jest.mock("~shared/hooks/useErrorDetails", () => mockErrorDetailsModule);

function renderController(onClose?: (result?: { success?: boolean }) => void) {
  return renderHook(() => useDeleteOrganizationController({ onClose }), {
    wrapper: createQueryClientWrapper(),
  });
}

describe("useDeleteOrganizationController", () => {
  const organization = makeOrganization({ id: "org-1" });

  it("initializes with no error and isPending=false", () => {
    const { result } = renderController();

    expect(result.current.error).toBeNull();
    expect(result.current.isPending).toBe(false);
  });

  it("remove calls deleteOrganization with the organization id", async () => {
    mockDeleteOrganization.mockResolvedValueOnce(OK_RESPONSE);
    const { result } = renderController();

    await act(async () => {
      await result.current.remove(organization);
    });

    expect(mockDeleteOrganization).toHaveBeenCalledWith("org-1");
  });

  it("calls onClose with success after a successful mutation", async () => {
    mockDeleteOrganization.mockResolvedValueOnce(OK_RESPONSE);
    const onClose = jest.fn();
    const { result } = renderController(onClose);

    await act(async () => {
      await result.current.remove(organization);
    });

    await waitFor(() => expect(onClose).toHaveBeenCalledWith({ success: true }));
  });

  it("sets error to getErrorMessage output when the mutation rejects", async () => {
    const failure = new Error("boom") as AxiosError;
    mockGetErrorMessage.mockReturnValue("readable failure");
    mockDeleteOrganization.mockRejectedValueOnce(failure);
    const { result } = renderController();

    await act(async () => {
      await result.current.remove(organization).catch(() => undefined);
    });

    await waitFor(() => expect(result.current.error).toBe("readable failure"));
    expect(mockGetErrorMessage).toHaveBeenCalledWith(failure);
  });

  it("clears a previous error after a successful retry", async () => {
    const failure = new Error("boom") as AxiosError;
    mockGetErrorMessage.mockReturnValue("readable failure");
    mockDeleteOrganization.mockRejectedValueOnce(failure);
    const onClose = jest.fn();
    const { result } = renderController(onClose);

    await act(async () => {
      await result.current.remove(organization).catch(() => undefined);
    });
    await waitFor(() => expect(result.current.error).toBe("readable failure"));

    mockDeleteOrganization.mockResolvedValueOnce(OK_RESPONSE);
    await act(async () => {
      await result.current.remove(organization);
    });

    await waitFor(() => expect(result.current.error).toBeNull());
  });

  it("handleCancel clears error and calls onClose without arguments when provided", () => {
    const onClose = jest.fn();
    const { result } = renderController(onClose);

    act(() => {
      result.current.handleCancel();
    });

    expect(onClose).toHaveBeenCalledWith();
  });

  it("handleCancel does nothing when onClose is not provided", () => {
    const { result } = renderController();

    expect(() => {
      act(() => {
        result.current.handleCancel();
      });
    }).not.toThrow();
  });
});
