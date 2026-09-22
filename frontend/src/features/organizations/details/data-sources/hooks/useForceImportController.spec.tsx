import { act, renderHook, waitFor } from "@testing-library/react";

import type { AxiosError } from "axios";

import type { useOrganizationsApi } from "~organizations/api";
import type { useErrorDetails } from "~shared/hooks/useErrorDetails";
import { createQueryClientWrapper, makeDatasource } from "~test-utils";

import { useForceImportController } from "./useForceImportController";

type OrganizationsApi = ReturnType<typeof useOrganizationsApi>;
type ErrorDetails = ReturnType<typeof useErrorDetails>;

const mockForceReimportDatasource = jest.fn() as jest.MockedFunction<
  OrganizationsApi["forceReimportDatasource"]
>;
const mockGetErrorMessage = jest.fn() as jest.MockedFunction<ErrorDetails["getErrorMessage"]>;

// The controller ignores the mutation's return value; give the typed mock a body-less
// stand-in rather than build a real AxiosResponse per test.
type ForceReimportResult = Awaited<ReturnType<OrganizationsApi["forceReimportDatasource"]>>;
const OK_RESPONSE = undefined as unknown as ForceReimportResult;

jest.mock("~organizations/api", () => ({
  useOrganizationsApi: () => ({ forceReimportDatasource: mockForceReimportDatasource }),
}));

jest.mock("~shared/hooks/useErrorDetails", () => ({
  useErrorDetails: () => ({ getErrorMessage: mockGetErrorMessage }),
}));

function renderController(onClose?: (result?: { success?: boolean }) => void) {
  return renderHook(() => useForceImportController({ onClose }), {
    wrapper: createQueryClientWrapper(),
  });
}

describe("useForceImportController", () => {
  const datasource = makeDatasource({ id: "ds-1" });

  it("initializes with no error, no lastImportAt, and isPending=false", () => {
    const { result } = renderController();

    expect(result.current.error).toBeNull();
    expect(result.current.lastImportAt).toBeUndefined();
    expect(result.current.isPending).toBe(false);
  });

  it("forceImport calls forceReimportDatasource without body when lastImportAt is unset", async () => {
    mockForceReimportDatasource.mockResolvedValueOnce(OK_RESPONSE);
    const { result } = renderController();

    act(() => {
      result.current.forceImport({ organizationId: "org-1", datasource });
    });

    await waitFor(() =>
      expect(mockForceReimportDatasource).toHaveBeenCalledWith("org-1", "ds-1", undefined),
    );
  });

  it("forceImport sends last_import_at as an ISO date string when lastImportAt is set", async () => {
    mockForceReimportDatasource.mockResolvedValueOnce(OK_RESPONSE);
    const { result } = renderController();
    console.log(result);
    act(() => {
      result.current.setLastImportAt(new Date(2026, 2, 15));
    });
    act(() => {
      result.current.forceImport({ organizationId: "org-1", datasource });
    });

    await waitFor(() =>
      expect(mockForceReimportDatasource).toHaveBeenCalledWith("org-1", "ds-1", {
        last_import_at: "2026-03-15",
      }),
    );
  });

  it("clears a prior error when forceImport is invoked again", async () => {
    mockGetErrorMessage.mockReturnValue("first failure");
    mockForceReimportDatasource.mockRejectedValueOnce(new Error("boom") as AxiosError);
    const { result } = renderController();

    act(() => {
      result.current.forceImport({ organizationId: "org-1", datasource });
    });
    await waitFor(() => expect(result.current.error).toBe("first failure"));

    mockForceReimportDatasource.mockResolvedValueOnce(OK_RESPONSE);
    act(() => {
      result.current.forceImport({ organizationId: "org-1", datasource });
    });

    await waitFor(() => expect(result.current.error).toBeNull());
  });

  it("calls onClose with success and resets state after a successful mutation", async () => {
    mockForceReimportDatasource.mockResolvedValueOnce(OK_RESPONSE);
    const onClose = jest.fn();
    const { result } = renderController(onClose);
    act(() => {
      result.current.setLastImportAt(new Date(2026, 2, 15));
    });

    act(() => {
      result.current.forceImport({ organizationId: "org-1", datasource });
    });

    await waitFor(() => expect(onClose).toHaveBeenCalledWith({ success: true }));
    expect(result.current.lastImportAt).toBeUndefined();
    expect(result.current.error).toBeNull();
  });

  it("does not throw on successful mutation when onClose is not provided", async () => {
    mockForceReimportDatasource.mockResolvedValueOnce(OK_RESPONSE);
    const { result } = renderController();

    act(() => {
      result.current.forceImport({ organizationId: "org-1", datasource });
    });

    await waitFor(() => expect(mockForceReimportDatasource).toHaveBeenCalled());
    expect(result.current.error).toBeNull();
  });

  it("sets error to getErrorMessage output when the mutation rejects", async () => {
    const failure = new Error("boom") as AxiosError;
    mockGetErrorMessage.mockReturnValue("readable failure");
    mockForceReimportDatasource.mockRejectedValueOnce(failure);
    const { result } = renderController();

    act(() => {
      result.current.forceImport({ organizationId: "org-1", datasource });
    });

    await waitFor(() => expect(result.current.error).toBe("readable failure"));
    expect(mockGetErrorMessage).toHaveBeenCalledWith(failure);
  });

  it("cancel resets state and calls onClose without arguments when onClose is provided", () => {
    const onClose = jest.fn();
    const { result } = renderController(onClose);
    act(() => {
      result.current.setLastImportAt(new Date(2026, 2, 15));
    });

    act(() => {
      result.current.cancel();
    });

    expect(onClose).toHaveBeenCalledWith();
    expect(result.current.lastImportAt).toBeUndefined();
    expect(result.current.error).toBeNull();
  });

  it("cancel only resets state when onClose is not provided", () => {
    const { result } = renderController();
    act(() => {
      result.current.setLastImportAt(new Date(2026, 2, 15));
    });

    act(() => {
      result.current.cancel();
    });

    expect(result.current.lastImportAt).toBeUndefined();
  });

  it("reset clears both error and lastImportAt", async () => {
    mockGetErrorMessage.mockReturnValue("boom");
    mockForceReimportDatasource.mockRejectedValueOnce(new Error("boom") as AxiosError);
    const { result } = renderController();
    act(() => {
      result.current.setLastImportAt(new Date(2026, 2, 15));
    });
    act(() => {
      result.current.forceImport({ organizationId: "org-1", datasource });
    });
    await waitFor(() => expect(result.current.error).toBe("boom"));

    act(() => {
      result.current.reset();
    });

    expect(result.current.error).toBeNull();
    expect(result.current.lastImportAt).toBeUndefined();
  });
});
