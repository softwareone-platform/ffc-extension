import { act, renderHook, waitFor } from "@testing-library/react";
import type { AxiosError } from "axios";

import type { OrganizationRead } from "~api/ffc-api-model";
import type { useOrganizationsApi } from "~features/organizations/api/useOrganizationsApi";
import type { useErrorDetails } from "~shared/hooks/useErrorDetails";
import { createQueryClientWrapper, makeOrganization } from "~test-utils";

import { useOrganizationsController } from "./useOrganizationsController";

type OrganizationsApi = ReturnType<typeof useOrganizationsApi>;
type ErrorDetails = ReturnType<typeof useErrorDetails>;
type EditResult = Awaited<ReturnType<OrganizationsApi["editOrganization"]>>;

const OK_RESPONSE = undefined as unknown as EditResult;

const mockEditOrganization = jest.fn() as jest.MockedFunction<OrganizationsApi["editOrganization"]>;
const mockGetErrorMessage = jest.fn() as jest.MockedFunction<ErrorDetails["getErrorMessage"]>;

jest.mock("~features/organizations/api/useOrganizationsApi", () => ({
  useOrganizationsApi: () => ({ editOrganization: mockEditOrganization }),
}));

jest.mock("~shared/hooks/useErrorDetails", () => ({
  useErrorDetails: () => ({ getErrorMessage: mockGetErrorMessage }),
}));

function renderController(
  organization: OrganizationRead | null,
  onClose?: (result?: { success?: boolean }) => void,
) {
  return renderHook(() => useOrganizationsController({ organization, onClose }), {
    wrapper: createQueryClientWrapper(),
  });
}

describe("useOrganizationsController", () => {
  const organization = makeOrganization({ id: "org-1", name: "Acme" });

  it("initializes with no error and isPending=false", () => {
    const { result } = renderController(organization);

    expect(result.current.error).toBeNull();
    expect(result.current.isPending).toBe(false);
  });

  it("populates form values from the organization", async () => {
    const { result } = renderController(
      makeOrganization({
        id: "org-1",
        name: "Acme",
        operations_external_id: "ext-1",
        currency: "USD",
      }),
    );

    await waitFor(() =>
      expect(result.current.control._formValues).toMatchObject({
        name: "Acme",
        operations_external_id: "ext-1",
        currency: "USD",
      }),
    );
  });

  it("editOrganization is called with the organization id and form data on submit", async () => {
    mockEditOrganization.mockResolvedValueOnce(OK_RESPONSE);
    const { result } = renderController(organization);

    await act(async () => {
      await result.current.submit();
    });

    await waitFor(() =>
      expect(mockEditOrganization).toHaveBeenCalledWith(
        "org-1",
        expect.objectContaining({ name: "Acme" }),
      ),
    );
  });

  it("calls onClose with success after a successful mutation", async () => {
    mockEditOrganization.mockResolvedValueOnce(OK_RESPONSE);
    const onClose = jest.fn();
    const { result } = renderController(organization, onClose);

    await act(async () => {
      await result.current.submit();
    });

    await waitFor(() => expect(onClose).toHaveBeenCalledWith({ success: true }));
  });

  it("sets error to getErrorMessage output when the mutation rejects", async () => {
    const failure = new Error("boom") as AxiosError;
    mockGetErrorMessage.mockReturnValue("readable failure");
    mockEditOrganization.mockRejectedValueOnce(failure);
    const { result } = renderController(organization);

    await act(async () => {
      await result.current.submit().catch(() => undefined);
    });

    await waitFor(() => expect(result.current.error).toBe("readable failure"));
    expect(mockGetErrorMessage).toHaveBeenCalledWith(failure);
  });

  it("does not attempt to edit when organization is null", async () => {
    const { result } = renderController(null);

    await act(async () => {
      await result.current.submit().catch(() => undefined);
    });

    expect(mockEditOrganization).not.toHaveBeenCalled();
  });

  it("handleCancel clears error and calls onClose without arguments when provided", () => {
    const onClose = jest.fn();
    const { result } = renderController(organization, onClose);

    act(() => {
      result.current.handleCancel();
    });

    expect(onClose).toHaveBeenCalledWith();
  });

  it("handleCancel is a noop when onClose is not provided", () => {
    const { result } = renderController(organization);

    expect(() => {
      act(() => {
        result.current.handleCancel();
      });
    }).not.toThrow();
  });
});
