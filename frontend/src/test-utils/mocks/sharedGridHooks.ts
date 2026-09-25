import type { useGridInfoDialogConfiguration } from "~shared/hooks/useGridInfoDialogConfiguration";

// `useReactQueryRqlGrid` is generic — typing the spy via `jest.MockedFunction<typeof ...>`
// instantiates every generic to its default. Leave it untyped so callers can drive it freely.
// (See SKILL.md "Type `jest.fn()` spies with the real signature — Generic hooks".)
export const mockUseReactQueryRqlGrid = jest.fn();

export const mockReactQueryRqlGridModule = {
  useReactQueryRqlGrid: (...args: unknown[]) => mockUseReactQueryRqlGrid(...args),
};

// useGridIdentity is a pure function; the mock returns an identity object.
// Callers that want to assert on the passed id can spy on the exported fn.
export const mockUseGridIdentity = jest.fn((id: string) => ({
  id,
  memoizeId: id,
  storageParameters: ["unknown"],
}));

export const mockGridIdentityModule = {
  useGridIdentity: (id: string) => mockUseGridIdentity(id),
};

export const mockUseGridInfoDialogConfiguration = jest.fn() as jest.MockedFunction<
  typeof useGridInfoDialogConfiguration
>;

export const mockGridInfoDialogConfigurationModule = {
  useGridInfoDialogConfiguration: () => mockUseGridInfoDialogConfiguration(),
};
