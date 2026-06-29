import { useEffect, useState } from "react";

import { List, Row, useListWithApi, UseListWithApiHookModel } from "@swo/design-system/list";
import { AccountRead } from "@swo/ffc-api-model";

import { useApiCall } from "~entitlements/create-entitlement-wizard/hooks/useApiCall";
import { useColumns } from "~entitlements/create-entitlement-wizard/hooks/useColumns";
import { useListDataWithSelectedEntity } from "~entitlements/create-entitlement-wizard/hooks/useListDataWithSelectedEntity";
import { Account } from "~features/entitlements/api/model";

const limitPerPage = 10;

export interface SelectAffiliateListProps {
  readonly entity: Account | null;
  readonly onSelected: (entity: Account) => void;
}

export function SelectAffiliateList({ entity, onSelected }: SelectAffiliateListProps) {
  const [selectedRows, setSelectedRows] = useState<Row<Account>[]>(
    entity ? [{ data: entity, selected: true }] : [],
  );
  const columns = useColumns();
  const apiCallRql = useApiCall(columns);

  const listProps = useListWithApi({
    apiCall: apiCallRql,
    limit: limitPerPage,
    columns,
  } as UseListWithApiHookModel<AccountRead>);

  useEffect(() => {
    if (selectedRows[0]) {
      onSelected(selectedRows[0].data);
    }
  }, [onSelected, selectedRows]);

  const data = useListDataWithSelectedEntity({ entity, data: listProps.data });

  return (
    <List<AccountRead>
      columns={listProps.columns || []}
      {...listProps}
      data={data}
      showFilterBar={true}
      trackBy="id"
      selectionType="radio"
      selectedRows={selectedRows}
      setSelectedRows={setSelectedRows}
      showSelectedNumber={false}
    />
  );
}
