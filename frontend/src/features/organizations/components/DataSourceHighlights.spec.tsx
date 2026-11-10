import { render, screen, within } from "@testing-library/react";

import type { DatasourceDetailRead, OrganizationRead } from "~api/ffc-api-model";
import { makeDatasourceDetail, makeOrganization } from "~test-utils";

import {
  mockUseDataSourceApi,
  mockUseFormatMoney,
  mockUseOrganizationDetailsApi,
} from "./DataSourceHighlights.spec.mocks";

import type { useDataSourceApi } from "../api/useDataSourceApi";
import type { useOrganizationDetailsApi } from "../api/useOrganizationDetailsApi";
import { DataSourceHighlights } from "./DataSourceHighlights";

const HIGHLIGHT_TITLES = [
  "resourcesChargedThisMonth",
  "expensesThisMonth",
  "forecastThisMonth",
] as const;

function prime({
  organization,
  dataSource,
}: {
  organization?: OrganizationRead;
  dataSource?: DatasourceDetailRead;
}) {
  mockUseOrganizationDetailsApi.mockReturnValue({
    data: organization,
  } as unknown as ReturnType<typeof useOrganizationDetailsApi>);
  mockUseDataSourceApi.mockReturnValue({
    data: dataSource,
  } as unknown as ReturnType<typeof useDataSourceApi>);
}

function renderHighlights() {
  return render(<DataSourceHighlights organizationId="org-1" dataSourceId="ds-1" />);
}

function highlightValues() {
  return screen
    .getAllByTestId("highlight-item")
    .slice(-HIGHLIGHT_TITLES.length)
    .map((item) => within(item).getByTestId("highlight-value").textContent);
}

describe("DataSourceHighlights", () => {
  beforeEach(() => {
    mockUseFormatMoney.mockReturnValue((value) => `formatted(${value ?? 0})`);
  });

  it("queries the organization and the data source by their ids", () => {
    prime({});

    renderHighlights();

    expect(mockUseOrganizationDetailsApi).toHaveBeenCalledWith("org-1");
    expect(mockUseDataSourceApi).toHaveBeenCalledWith("org-1", "ds-1");
  });

  it("renders a Skeleton while the data source is not loaded", () => {
    prime({ organization: makeOrganization() });

    renderHighlights();

    expect(screen.getByTestId("skeleton")).toBeInTheDocument();
    expect(screen.queryByTestId("in-page-highlight")).not.toBeInTheDocument();
  });

  it("formats expenses with the organization currency in non-symbol mode", () => {
    prime({
      organization: makeOrganization({ currency: "EUR" }),
      dataSource: makeDatasourceDetail(),
    });

    renderHighlights();

    expect(mockUseFormatMoney).toHaveBeenCalledWith("EUR", false);
  });

  it("renders the untitled organization reference before the data source figures", () => {
    prime({
      organization: makeOrganization({ id: "org-1", name: "Acme" }),
      dataSource: makeDatasourceDetail(),
    });

    renderHighlights();

    const titles = screen.getAllByTestId("highlight-title").map((el) => el.textContent);
    expect(titles).toEqual(["", ...HIGHLIGHT_TITLES]);
    expect(screen.getByTestId("primary")).toHaveTextContent("Acme");
    expect(screen.getByTestId("secondary")).toHaveTextContent("org-1");
  });

  it("omits the organization reference when the organization is not loaded", () => {
    prime({ dataSource: makeDatasourceDetail() });

    renderHighlights();

    expect(screen.queryByTestId("entity-reference-cell")).not.toBeInTheDocument();
    expect(screen.getAllByTestId("highlight-item")).toHaveLength(HIGHLIGHT_TITLES.length);
  });

  it("renders the charged resources count and formatted expenses followed by the currency", () => {
    prime({
      organization: makeOrganization({ currency: "USD" }),
      dataSource: makeDatasourceDetail({
        resources_charged_this_month: 7,
        expenses_so_far_this_month: 50,
        expenses_forecast_this_month: 75,
      }),
    });

    renderHighlights();

    expect(highlightValues()).toEqual(["7 ", "formatted(50) USD", "formatted(75) USD"]);
  });

  it("defaults missing figures to 0", () => {
    const dataSource = {
      id: "ds-1",
      resources_charged_this_month: undefined,
      expenses_so_far_this_month: undefined,
      expenses_forecast_this_month: undefined,
    } as unknown as DatasourceDetailRead;
    prime({ organization: makeOrganization({ currency: "USD" }), dataSource });

    renderHighlights();

    expect(highlightValues()).toEqual(["0 ", "formatted(0) USD", "formatted(0) USD"]);
  });
});
