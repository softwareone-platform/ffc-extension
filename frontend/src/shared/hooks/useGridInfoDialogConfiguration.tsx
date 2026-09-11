import { useMemo } from "react";

import { useDefaultInfoDialogConfiguration } from "@swo/design-system/grid";

import { useFixedT } from "./useFixedT";

export function useGridInfoDialogConfiguration() {
  const { defaultNoDataConfiguration } = useDefaultInfoDialogConfiguration();
  const t = useFixedT("shared:grid");

  return useMemo(() => {
    return {
      noDataConfiguration: {
        ...defaultNoDataConfiguration,
        description: t("infoDialog:noData:description"),
        button: undefined,
      },
    };
  }, [defaultNoDataConfiguration]);
}
