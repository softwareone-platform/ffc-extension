import { useCallback } from "react";

import { ListOption } from "@swo/design-system/dropdown";

import { DatasourceRead } from "~api/ffc-api-model";
import { DatasourceAction } from "~features/organizations/api/model";
import { RoleAwareAction, useActionsByRole } from "~shared/hooks/useActionsByRole";
import { useFixedT } from "~shared/hooks/useFixedT";

import { isForceImportEnabled } from "../constants";

export function useActionOptions(): (entity: DatasourceRead) => ListOption<DatasourceAction>[] {
  const tActions = useFixedT("shared:actions");
  const filterActionsByRole = useActionsByRole<DatasourceAction>();

  return useCallback(
    (item: DatasourceRead): ListOption<DatasourceAction>[] => {
      const actions: RoleAwareAction<DatasourceAction>[] = [
        {
          label: tActions("force_import"),
          value: "force_import",
          isDisabled: !isForceImportEnabled(item.type),
          requiredRoles: ["admin"],
        },
      ];

      return filterActionsByRole(actions);
    },
    [filterActionsByRole, tActions],
  );
}
