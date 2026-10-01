import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

import type { Account } from "~features/entitlements/api/model";
import { makeAccount } from "~test-utils";

import {
  mockList,
  mockUseApiCall,
  mockUseColumns,
  mockUseListDataWithSelectedEntity,
  mockUseListWithApi,
  nextSelectedAccount,
} from "./SelectAffiliateList.spec.mocks";

import { SelectAffiliateList } from "./SelectAffiliateList";

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

  it("preselects the current entity and configures the list with merged affiliate data", () => {
    const entity = makeAccount({ id: "acc-1", name: "Selected" }) as Account;
    const onSelected = jest.fn();

    render(<SelectAffiliateList entity={entity} onSelected={onSelected} />);

    expect(mockUseApiCall).toHaveBeenCalledWith(columns);
    expect(mockUseListWithApi).toHaveBeenCalledWith({ apiCall, limit: 10, columns });
    expect(mockUseListDataWithSelectedEntity).toHaveBeenCalledWith({ entity, data: listData });
    expect(mockList).toHaveBeenCalledWith(
      expect.objectContaining({
        data: mergedData,
        selectedRows: [{ data: entity, selected: true }],
        selectionType: "radio",
        trackBy: "id",
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
    expect(onSelected).not.toHaveBeenCalled();
    expect(screen.getByTestId("selected-count")).toHaveTextContent("0");
  });

  it("reports the newly selected row when the list selection changes", async () => {
    const user = userEvent.setup();
    const onSelected = jest.fn();

    render(<SelectAffiliateList entity={null} onSelected={onSelected} />);

    await user.click(screen.getByRole("button", { name: "choose next" }));

    expect(onSelected).toHaveBeenCalledWith(nextSelectedAccount);
    expect(screen.getByTestId("selected-count")).toHaveTextContent("1");
  });
});
