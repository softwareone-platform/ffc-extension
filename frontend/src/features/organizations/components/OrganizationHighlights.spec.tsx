import { render, screen, within } from "@testing-library/react";

import type { OrganizationRead } from "~api/ffc-api-model";
import type { useOrganizationDetailsApi } from "~organizations/api";

import {
  mockUseFormatMoney,
  mockUseOrganizationDetailsApi,
} from "./OrganizationHighlights.spec.mocks";

import { OrganizationHighlights } from "./OrganizationHighlights";

type UseOrganizationDetailsApiResult = ReturnType<typeof useOrganizationDetailsApi>;

const HIGHLIGHT_TITLES = [
  "limit",
  "expensesThisMonth",
  "forecastThisMonth",
  "possibleSavings",
] as const;

function primeEntity(entity: Partial<OrganizationRead> | undefined) {
  mockUseOrganizationDetailsApi.mockReturnValue({
    data: entity,
  } as unknown as UseOrganizationDetailsApiResult);
}

describe("OrganizationHighlights", () => {
  beforeEach(() => {
    mockUseFormatMoney.mockReturnValue((value) => `formatted(${value ?? 0})`);
  });

  it("queries organization details for the supplied organizationId", () => {
    primeEntity(undefined);

    render(<OrganizationHighlights organizationId="org-1" />);

    expect(mockUseOrganizationDetailsApi).toHaveBeenCalledWith("org-1");
  });

  it("renders a Skeleton while the entity is not loaded", () => {
    primeEntity(undefined);

    render(<OrganizationHighlights organizationId="org-1" />);

    expect(screen.getByTestId("skeleton")).toBeInTheDocument();
    expect(screen.queryByTestId("highlights")).not.toBeInTheDocument();
  });

  it("renders four highlight items in fixed order when the entity has an id", () => {
    primeEntity({
      id: "org-1",
      currency: "USD",
      expenses_info: {
        limit: "100",
        expenses_this_month: "50",
        expenses_this_month_forecast: "75",
        possible_monthly_saving: "10",
      },
    });

    render(<OrganizationHighlights organizationId="org-1" />);

    const titles = screen.getAllByTestId("highlight-title").map((el) => el.textContent);
    expect(titles).toEqual([...HIGHLIGHT_TITLES]);
  });

  it("passes entity.currency and non-symbol mode to useFormatMoney", () => {
    primeEntity({ id: "org-1", currency: "EUR" });

    render(<OrganizationHighlights organizationId="org-1" />);

    expect(mockUseFormatMoney).toHaveBeenCalledWith("EUR", false);
  });

  it("renders each expense figure through the formatter followed by the currency", () => {
    primeEntity({
      id: "org-1",
      currency: "USD",
      expenses_info: {
        limit: "100",
        expenses_this_month: "50",
        expenses_this_month_forecast: "75",
        possible_monthly_saving: "10",
      },
    });

    render(<OrganizationHighlights organizationId="org-1" />);

    const items = screen.getAllByTestId("highlight-item");
    const values = items.map((item) => within(item).getByTestId("highlight-value").textContent);
    expect(values).toEqual([
      "formatted(100) USD",
      "formatted(50) USD",
      "formatted(75) USD",
      "formatted(10) USD",
    ]);
  });

  it("defaults each figure to 0 when expenses_info is missing", () => {
    primeEntity({ id: "org-1", currency: "USD" });

    render(<OrganizationHighlights organizationId="org-1" />);

    const values = screen.getAllByTestId("highlight-value").map((el) => el.textContent);
    expect(values.every((v) => v === "formatted(0) USD")).toBe(true);
  });
});
