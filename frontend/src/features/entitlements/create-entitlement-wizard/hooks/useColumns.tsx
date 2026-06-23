import { EntityReference } from "@swo/design-system/entity-reference";
import { Column } from "@swo/design-system/list";
import { AccountRead } from "@swo/ffc-api-model";

const columns: Column<AccountRead>[] = [
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
          />
        </>
      );
    },
  },
];

// eslint-disable-next-line @eslint-react/no-unnecessary-use-prefix
export function useColumns(): Column<AccountRead>[] {
  return columns;
}
