import { useMemo } from "react";

import {
  GridCellSimple,
  GridColumnDefinition,
  GridInMemoryConfig,
  useGridInMemory,
} from "@swo/design-system/grid";
import { Icon } from "@swo/design-system/icon";

import { MicrosoftAccount, microsoftAccounts } from "./microsoft-accounts.mock";

const SEARCHABLE_FIELDS = ["name", "microsoftId", "domainName"];

function useColumns(): GridColumnDefinition<MicrosoftAccount>[] {
  return useMemo(
    () => [
      {
        name: "name",
        title: "Name",
        cell: (item: MicrosoftAccount) => <GridCellSimple>{item.name}</GridCellSimple>,
        initialWidth: 320,
      },
      {
        name: "microsoftId",
        title: "Microsoft ID",
        cell: (item: MicrosoftAccount) => <GridCellSimple>{item.microsoftId}</GridCellSimple>,
        initialWidth: 360,
      },
      {
        name: "domainName",
        title: "Domain name",
        cell: (item: MicrosoftAccount) => <GridCellSimple>{item.domainName}</GridCellSimple>,
        initialWidth: 320,
      },
      {
        name: "actions",
        type: "Actions",
        title: "",
        cell: () => (
          <GridCellSimple>
            <Icon name="more_horiz" size={18} />
          </GridCellSimple>
        ),
        initialWidth: 56,
        isScalable: false,
      },
    ],
    [],
  );
}

export function useGridConfig() {
  const columns = useColumns();

  const config = useMemo(
    (): GridInMemoryConfig<MicrosoftAccount> => ({
      id: "grid__cloud-iq-microsoft-accounts",
      columns,
      search: {
        fields: SEARCHABLE_FIELDS,
        apply: (term) => {
          if (!term) return null;
          return {
            operator: "or",
            value: SEARCHABLE_FIELDS.map((field) => ({
              field,
              operator: "contains",
              value: term,
            })),
          };
        },
      },
    }),
    [columns],
  );

  return useGridInMemory<MicrosoftAccount>(microsoftAccounts, config);
}
