import { useMemo } from "react";
import { useFixedT } from "../../../shared/hooks/useFixedT";

export function useViews() {
  const tView = useFixedT("shared:grid:views");

  return useMemo(() => {
    return [
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
  }, []);
}
