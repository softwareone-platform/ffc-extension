import { EntityReference } from "@swo/design-system/entity-reference";
import { Column } from "@swo/design-system/list";

import { Account } from "~features/entitlements/api/model";
import AccountTypeIcon from "~shared/components/account-type-icons/AccountTypeIcon";

const columns: Column<Account>[] = [
  { name: "id", filterable: true, hide: true },
  {
    name: "name",
    filterable: true,
    cell: (item) => {
      const data = item.data;
      return (
        <>
          <EntityReference
            primaryContent={data.name}
            secondaryContent={data.id}
            isPrimaryContentBold={false}
            icon={<AccountTypeIcon name={data.integration} size={44} />}
          />
        </>
      );
    },
  },
];

// eslint-disable-next-line @eslint-react/no-unnecessary-use-prefix
export function useColumns(): Column<Account>[] {
  return columns;
}
