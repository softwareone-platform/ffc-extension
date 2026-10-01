import type { ComponentProps } from "react";

import { screen } from "@testing-library/react";

import type { EntitlementHighlights } from "~features/entitlements/components/EntitlementHighlights";
import { renderWithEntitlementRoute, renderWithRouter } from "~test-utils";

import { EntitlementDetailsContent } from "./DetailsContent";

type MockNavigationTopBarProps = ComponentProps<
  typeof import("@swo/design-system/navigation").Navigation.TopBar
>;
type MockCardProps = ComponentProps<typeof import("@swo/design-system/card").Card>;
type MockHighlightsProps = ComponentProps<typeof EntitlementHighlights>;

const mockHighlights = jest.fn() as jest.MockedFunction<(props: MockHighlightsProps) => void>;
const mockTopBar = jest.fn() as jest.MockedFunction<(props: MockNavigationTopBarProps) => void>;

jest.mock("../components/EntitlementHighlights", () => ({
  EntitlementHighlights: (props: MockHighlightsProps) => {
    mockHighlights(props);
    return <div data-testid="entitlement-highlights">{props.entitlementId}</div>;
  },
}));

jest.mock("@swo/design-system/card", () => ({
  Card: ({ children }: MockCardProps) => <div data-testid="card">{children}</div>,
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
    renderWithEntitlementRoute(<EntitlementDetailsContent />, {
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
    renderWithEntitlementRoute(<EntitlementDetailsContent />, {
      routePath: "/entitlements/:entitlementId/*",
    });

    const paths = mockTopBar.mock.lastCall![0].items!.map((item) => item.path);
    expect(paths).toEqual(["general", "events"]);
  });
});
