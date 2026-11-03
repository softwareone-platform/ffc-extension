import { DatasourceDetailRead, DatasourceRead } from "~api/ffc-api-model";

export function makeDatasource(overrides: Partial<DatasourceRead> = {}): DatasourceRead {
  return {
    id: "ds-1",
    name: "AWS Prod",
    type: "aws_cnr",
    datasource_id: "aws-prod-123",
    resources_charged_this_month: 0,
    expenses_so_far_this_month: 0,
    expenses_forecast_this_month: 0,
    ...overrides,
  };
}

export function makeDatasourceDetail(
  overrides: Partial<DatasourceDetailRead> = {},
): DatasourceDetailRead {
  return {
    id: "ds-1",
    name: "AWS Prod",
    type: "aws_cnr",
    datasource_id: "aws-prod-123",
    resources_charged_this_month: 0,
    expenses_so_far_this_month: 0,
    expenses_forecast_this_month: 0,
    billing: { status: "unknown" },
    metrics: { status: "unknown" },
    ...overrides,
  };
}
