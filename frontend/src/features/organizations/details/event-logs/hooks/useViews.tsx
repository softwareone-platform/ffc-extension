import { useMemo } from "react";

import { useFixedT } from "~shared/hooks/useFixedT";

export function useViews() {
  const tView = useFixedT("shared:grid:views");

  return useMemo(() => {
    return [
      {
        name: "logInfo",
        title: tView("logEventInfo"),
        configuration: {
          filters: {
            operator: "and",
            value: [{ operator: "eq", field: "level", value: "INFO" }],
          },
          sort: [{ field: "time", direction: "desc" }],
        },
      },
      {
        name: "logWarning",
        title: tView("logEventWarning"),
        configuration: {
          filters: {
            operator: "and",
            value: [{ operator: "eq", field: "level", value: "WARNING" }],
          },
          sort: [{ field: "time", direction: "desc" }],
        },
      },
      {
        name: "logError",
        title: tView("logEventError"),
        configuration: {
          filters: {
            operator: "and",
            value: [{ operator: "eq", field: "level", value: "ERROR" }],
          },
          sort: [{ field: "time", direction: "desc" }],
        },
      },
    ];
  }, [tView]);
}
