import { useMemo } from "react";

import { useFixedT } from "~shared/hooks/useFixedT";

export function useViews() {
  const tView = useFixedT("shared:grid:views");

  return useMemo(() => {
    return [
      {
        name: "main",
        title: tView("mainOrganizations"),
        configuration: {
          filters: {
            operator: "or",
            value: [{ operator: "neq", field: "status", value: "deleted" }],
          },
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
  }, [tView]);
}
