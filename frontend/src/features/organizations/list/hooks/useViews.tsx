import { useMemo } from "react";

import { useSearchParams } from "react-router-dom";

import type { OrganizationStatus } from "~api/ffc-api-model";
import { LIST_PARAMS } from "~organizations/paths";
import { useFixedT } from "~shared/hooks/useFixedT";

const STATUSES: OrganizationStatus[] = ["active", "terminated", "deleted"];

// `?statuses=active,terminated` (e.g. from the dashboard) replaces the main view's filter.
function statusFilterFromParam(param: string | null) {
  const picks = new Set(param?.split(",") ?? []);
  const statuses = STATUSES.filter((status) => picks.has(status));
  if (statuses.length === 0) {
    return { operator: "or", value: [{ operator: "neq", field: "status", value: "deleted" }] };
  }
  return {
    operator: "or",
    value: statuses.map((status) => ({ operator: "eq", field: "status", value: status })),
  };
}

export function useViews() {
  const tView = useFixedT("shared:grid:views");
  const [searchParams] = useSearchParams();
  const statusParam = searchParams.get(LIST_PARAMS.statuses);

  return useMemo(() => {
    return [
      {
        name: "main",
        title: tView("mainOrganizations"),
        configuration: {
          filters: statusFilterFromParam(statusParam),
          sort: [{ field: "events.updated.at", direction: "desc" }],
        },
      },
      {
        name: "active",
        title: tView("activeOrganizations"),
        configuration: {
          filters: {
            operator: "and",
            value: [{ operator: "eq", field: "status", value: "active" }],
          },
          sort: [{ field: "name", direction: "asc" }],
        },
      },
      {
        name: "deleted",
        title: tView("deletedOrganizations"),
        configuration: {
          filters: {
            operator: "and",
            value: [{ operator: "eq", field: "status", value: "deleted" }],
          },
          sort: [{ field: "name", direction: "asc" }],
        },
      },
    ];
  }, [tView, statusParam]);
}
