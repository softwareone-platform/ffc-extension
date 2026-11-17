import { render, screen, within } from "@testing-library/react";

import type { OrganizationRead } from "~api/ffc-api-model";
import type { useOrganizationDetailsApi } from "~organizations/api";
import { makeClientAccount } from "~test-utils";
import { mockDesignSystemUtilsGlobals } from "~test-utils/mocks/designSystemUtils";

import {
  mockUseFormatMoney,
  mockUseOrganizationDetailsApi,
} from "./OrganizationHighlights.spec.mocks";

import { OrganizationHighlights } from "./OrganizationHighlights";

const { NO_VALUE } = mockDesignSystemUtilsGlobals;

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
    expect(screen.queryByTestId("in-page-highlight")).not.toBeInTheDocument();
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

  it("does not render a client highlight when the entity has no client", () => {
    primeEntity({ id: "org-1", currency: "USD", client: null });

    render(<OrganizationHighlights organizationId="org-1" />);

    expect(screen.queryByTestId("entity-reference-cell")).not.toBeInTheDocument();
    expect(screen.getAllByTestId("highlight-item")).toHaveLength(HIGHLIGHT_TITLES.length);
  });

  it("renders an untitled client highlight before the expense figures when the entity has a client", () => {
    primeEntity({ id: "org-1", currency: "USD", client: makeClientAccount() });

    render(<OrganizationHighlights organizationId="org-1" />);

    const titles = screen.getAllByTestId("highlight-title").map((el) => el.textContent);
    expect(titles).toEqual(["", ...HIGHLIGHT_TITLES]);
    expect(
      within(screen.getAllByTestId("highlight-item")[0]).getByTestId("entity-reference-cell"),
    ).toBeInTheDocument();
  });

  it("renders the client name, external_id and a square icon avatar", () => {
    primeEntity({
      id: "org-1",
      currency: "USD",
      client: makeClientAccount({ name: "Client Co", external_id: "cli-ext-1", icon: "a.png" }),
    });

    render(<OrganizationHighlights organizationId="org-1" />);

    expect(screen.getByTestId("primary")).toHaveTextContent("Client Co");
    expect(screen.getByTestId("secondary")).toHaveTextContent("cli-ext-1");
    expect(screen.getByTestId("avatar")).toHaveAttribute("data-image-src", "/public/a.png");
  });

  it("omits the client avatar when the client has no icon", () => {
    primeEntity({ id: "org-1", currency: "USD", client: makeClientAccount({ icon: undefined }) });

    render(<OrganizationHighlights organizationId="org-1" />);

    expect(screen.getByTestId("entity-reference-cell")).toBeInTheDocument();
    expect(screen.queryByTestId("avatar")).not.toBeInTheDocument();
  });

  it("falls back to NO_VALUE as client secondary content when external_id is empty", () => {
    primeEntity({ id: "org-1", currency: "USD", client: makeClientAccount({ external_id: "" }) });

    render(<OrganizationHighlights organizationId="org-1" />);

    expect(screen.getByTestId("secondary")).toHaveTextContent(NO_VALUE);
  });
});
