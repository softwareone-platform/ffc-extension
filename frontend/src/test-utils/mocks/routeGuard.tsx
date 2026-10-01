import type { RouteGuard } from "~shared/components/RouteGuard";

type MockRouteGuardProps = React.ComponentProps<typeof RouteGuard>;

export const mockRouteGuard = jest.fn() as jest.MockedFunction<
  (props: Pick<MockRouteGuardProps, "allowedRoles">) => void
>;

export const mockRouteGuardModule = {
  RouteGuard: ({ children, allowedRoles }: MockRouteGuardProps) => {
    mockRouteGuard({ allowedRoles });
    return <div data-testid="route-guard">{children}</div>;
  },
};
