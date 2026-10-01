import type { useUserRole } from "~shared/hooks/useUserRole";

export const mockUseUserRole = jest.fn() as jest.MockedFunction<typeof useUserRole>;

export const mockUserRoleModule = {
  useUserRole: () => mockUseUserRole(),
};
