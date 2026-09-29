import { render, screen, waitFor } from "@testing-library/react";

import { useFixedT } from "~shared/hooks/useFixedT";
import { mockFixedT } from "~test-utils/mocks/fixedT";
import { mockUserRoleModule, mockUseUserRole } from "~test-utils/mocks/userRole";

import { RouteGuard } from "./RouteGuard";

const mockHandleError = jest.fn();

jest.mock("~shared/hooks/useUserRole", () => mockUserRoleModule);

jest.mock("~shared/providers/ErrorHandlerProvider", () => ({
  useErrorHandler: () => ({ handleError: mockHandleError }),
}));

describe("RouteGuard", () => {
  beforeEach(() => {
    mockFixedT(jest.mocked(useFixedT));
  });

  it("renders children and allows an explicitly allowed single role", async () => {
    mockUseUserRole.mockReturnValue({ user: null, role: "admin" });

    render(
      <RouteGuard allowedRoles="admin">
        <div data-testid="child">child</div>
      </RouteGuard>,
    );

    expect(screen.getByTestId("child")).toBeInTheDocument();
    await waitFor(() => expect(mockHandleError).not.toHaveBeenCalled());
  });

  it("renders children and allows a role present in the allowed role list", async () => {
    mockUseUserRole.mockReturnValue({ user: null, role: "operations" });

    render(
      <RouteGuard allowedRoles={["admin", "operations"]}>
        <div data-testid="child">child</div>
      </RouteGuard>,
    );

    expect(screen.getByTestId("child")).toBeInTheDocument();
    await waitFor(() => expect(mockHandleError).not.toHaveBeenCalled());
  });

  it("reports a forbidden error when the role is missing", async () => {
    mockUseUserRole.mockReturnValue({ user: null, role: undefined });

    render(
      <RouteGuard allowedRoles={["admin"]}>
        <div data-testid="child">child</div>
      </RouteGuard>,
    );

    expect(screen.getByTestId("child")).toBeInTheDocument();
    await waitFor(() =>
      expect(mockHandleError).toHaveBeenCalledWith("403", "translated:description:forbidden"),
    );
  });

  it("reports a forbidden error when the role is not allowed", async () => {
    mockUseUserRole.mockReturnValue({ user: null, role: "affiliate" });

    render(
      <RouteGuard allowedRoles={["admin", "operations"]}>
        <div data-testid="child">child</div>
      </RouteGuard>,
    );

    await waitFor(() =>
      expect(mockHandleError).toHaveBeenCalledWith("403", "translated:description:forbidden"),
    );
  });

  it("does not report an error when no roles are required", async () => {
    mockUseUserRole.mockReturnValue({ user: null, role: undefined });

    render(
      <RouteGuard allowedRoles={[]}>
        <div data-testid="child">child</div>
      </RouteGuard>,
    );

    expect(screen.getByTestId("child")).toBeInTheDocument();
    await waitFor(() => expect(mockHandleError).not.toHaveBeenCalled());
  });
});
