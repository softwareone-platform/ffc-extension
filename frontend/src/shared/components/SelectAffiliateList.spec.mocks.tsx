import type { ComponentProps } from "react";

import type { List, useListWithApi } from "@swo/design-system/list";

import type { Account } from "~features/entitlements/api/model";
import type { useApiCall } from "~features/entitlements/create-entitlement-wizard/hooks/useApiCall";
import type { useListDataWithSelectedEntity } from "~features/entitlements/create-entitlement-wizard/hooks/useListDataWithSelectedEntity";
import { makeAccount } from "~test-utils";

type MockListProps = ComponentProps<typeof List>;

export const nextSelectedAccount = makeAccount({
  id: "acc-next",
  name: "Next Account",
}) as Account;

export const mockUseColumns = jest.fn();
export const mockUseApiCall = jest.fn();
export const mockUseListWithApi = jest.fn();
export const mockUseListDataWithSelectedEntity = jest.fn();
export const mockList = jest.fn() as jest.MockedFunction<(props: MockListProps) => void>;

jest.mock("~entitlements/create-entitlement-wizard/hooks/useColumns", () => ({
  useColumns: () => mockUseColumns(),
}));

jest.mock("~entitlements/create-entitlement-wizard/hooks/useApiCall", () => ({
  useApiCall: (...args: Parameters<typeof useApiCall>) => mockUseApiCall(...args),
}));

jest.mock("~entitlements/create-entitlement-wizard/hooks/useListDataWithSelectedEntity", () => ({
  useListDataWithSelectedEntity: (...args: Parameters<typeof useListDataWithSelectedEntity>) =>
    mockUseListDataWithSelectedEntity(...args),
}));

jest.mock("@swo/design-system/list", () => ({
  List: (props: MockListProps) => {
    mockList(props);
    return (
      <div data-testid="affiliate-list">
        <button
          onClick={() => props.setSelectedRows?.([{ data: nextSelectedAccount, selected: true }])}
        >
          choose next
        </button>
        <div data-testid="selected-count">{props.selectedRows?.length ?? 0}</div>
        <div data-testid="data-count">{props.data?.length ?? 0}</div>
      </div>
    );
  },
  useListWithApi: (...args: Parameters<typeof useListWithApi>) => mockUseListWithApi(...args),
}));
