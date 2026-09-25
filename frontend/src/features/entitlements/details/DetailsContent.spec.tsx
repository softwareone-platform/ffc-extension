import type { ComponentProps, ReactNode } from "react";

import { screen } from "@testing-library/react";

import { renderWithRouter } from "~test-utils";

import { EntitlementDetailsContent } from "./DetailsContent";

type MockNavigationTopBarProps = ComponentProps<
  typeof import("@swo/design-system/navigation").Navigation.TopBar
>;

const mockHighlights = jest.fn() as jest.MockedFunction<(props: { entitlementId: string }) => void>;
const mockTopBar = jest.fn() as jest.MockedFunction<(props: MockNavigationTopBarProps) => void>;

jest.mock("../components/EntitlementHighlights", () => ({
  EntitlementHighlights: (props: { entitlementId: string }) => {
    mockHighlights(props);
    return <div data-testid="entitlement-highlights">{props.entitlementId}</div>;
  },
}));

jest.mock("@swo/design-system/card", () => ({
  Card: ({ children }: { children?: ReactNode }) => <div data-testid="card">{children}</div>,
}));

jest.mock("@swo/design-system/navigation", () => ({
  Navigation: {
    TopBar: (props: MockNavigationTopBarProps) => {
      mockTopBar(props);
      return <nav data-testid="top-bar" />;
    },
  },
}));

describe("EntitlementDetailsContent", () => {
  it("renders EntitlementHighlights with the entitlementId when the param is present", () => {
    renderWithRouter(<EntitlementDetailsContent />, {
      initialUrl: "/entitlements/ent-1",
      routePath: "/entitlements/:entitlementId/*",
    });

    expect(mockHighlights).toHaveBeenCalledWith({ entitlementId: "ent-1" });
  });

  it("omits EntitlementHighlights when the entitlementId param is missing", () => {
    renderWithRouter(<EntitlementDetailsContent />, {
      initialUrl: "/entitlements",
      routePath: "/entitlements",
    });

    expect(mockHighlights).not.toHaveBeenCalled();
    expect(screen.queryByTestId("entitlement-highlights")).not.toBeInTheDocument();
  });

  it("renders the top bar with items for general and events in fixed order", () => {
    renderWithRouter(<EntitlementDetailsContent />, {
      initialUrl: "/entitlements/ent-1",
      routePath: "/entitlements/:entitlementId/*",
    });

    const paths = mockTopBar.mock.lastCall![0].items!.map((item) => item.path);
    expect(paths).toEqual(["general", "events"]);
  });
});
