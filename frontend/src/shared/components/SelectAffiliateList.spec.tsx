import type { ComponentProps } from "react";

import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import type { List, Row } from "@swo/design-system/list";

import type { Account } from "~features/entitlements/api/model";
import { makeAccount } from "~test-utils";

import { SelectAffiliateList } from "./SelectAffiliateList";

type MockListProps = ComponentProps<typeof List>;
type AccountRow = Row<Account>;

const mockUseColumns = jest.fn();
const mockUseApiCall = jest.fn();
const mockUseListWithApi = jest.fn();
const mockUseListDataWithSelectedEntity = jest.fn();
const mockList = jest.fn() as jest.MockedFunction<(props: MockListProps) => void>;

const nextSelectedAccount = makeAccount({ id: "acc-next", name: "Next Account" }) as Account;

jest.mock("~entitlements/create-entitlement-wizard/hooks/useColumns", () => ({
  useColumns: () => mockUseColumns(),
}));

jest.mock("~entitlements/create-entitlement-wizard/hooks/useApiCall", () => ({
  useApiCall: (...args: unknown[]) => mockUseApiCall(...args),
}));

jest.mock("~entitlements/create-entitlement-wizard/hooks/useListDataWithSelectedEntity", () => ({
  useListDataWithSelectedEntity: (...args: unknown[]) => mockUseListDataWithSelectedEntity(...args),
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
  useListWithApi: (...args: unknown[]) => mockUseListWithApi(...args),
}));

describe("SelectAffiliateList", () => {
  const columns = [{ name: "name" }, { name: "id" }];
  const apiCall = jest.fn();
  const listData = [makeAccount({ id: "acc-2", name: "Listed" }) as Account];
  const mergedData = [makeAccount({ id: "acc-3", name: "Merged" }) as Account];

  beforeEach(() => {
    mockUseColumns.mockReturnValue(columns);
    mockUseApiCall.mockReturnValue(apiCall);
    mockUseListWithApi.mockReturnValue({
      columns,
      data: listData,
      isLoading: false,
    });
    mockUseListDataWithSelectedEntity.mockReturnValue(mergedData);
  });

  it("seeds the selected row from the current entity and wires the list hooks", () => {
    const entity = makeAccount({ id: "acc-1", name: "Selected" }) as Account;
    const onSelected = jest.fn();

    render(<SelectAffiliateList entity={entity} onSelected={onSelected} />);

    expect(mockUseApiCall).toHaveBeenCalledWith(columns);
    expect(mockUseListWithApi).toHaveBeenCalledWith({ apiCall, limit: 10, columns });
    expect(mockUseListDataWithSelectedEntity).toHaveBeenCalledWith({ entity, data: listData });
    expect(mockList.mock.lastCall?.[0]).toEqual(
      expect.objectContaining({
        columns,
        data: mergedData,
        showFilterBar: true,
        trackBy: "id",
        selectionType: "radio",
        showSelectedNumber: false,
        selectedRows: [{ data: entity, selected: true }] satisfies AccountRow[],
      }),
    );
    expect(onSelected).toHaveBeenCalledWith(entity);
    expect(screen.getByTestId("selected-count")).toHaveTextContent("1");
    expect(screen.getByTestId("data-count")).toHaveTextContent("1");
  });

  it("starts without a selected row when no entity is provided", () => {
    const onSelected = jest.fn();

    render(<SelectAffiliateList entity={null} onSelected={onSelected} />);

    expect(mockUseListDataWithSelectedEntity).toHaveBeenCalledWith({
      entity: null,
      data: listData,
    });
    expect(mockList.mock.lastCall?.[0].selectedRows).toEqual([]);
    expect(onSelected).not.toHaveBeenCalled();
    expect(screen.getByTestId("selected-count")).toHaveTextContent("0");
  });

  it("reports the newly selected row when the list selection changes", async () => {
    const user = userEvent.setup();
    const onSelected = jest.fn();

    render(<SelectAffiliateList entity={null} onSelected={onSelected} />);

    await user.click(screen.getByRole("button", { name: "choose next" }));

    expect(onSelected).toHaveBeenCalledWith(nextSelectedAccount);
    expect(mockList.mock.lastCall?.[0].selectedRows).toEqual([
      { data: nextSelectedAccount, selected: true } satisfies AccountRow,
    ]);
    expect(screen.getByTestId("selected-count")).toHaveTextContent("1");
  });
});
