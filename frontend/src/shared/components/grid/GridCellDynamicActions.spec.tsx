import { render, screen } from "@testing-library/react";

import { GridCellDynamicActions } from "./GridCellDynamicActions";

const mockGridCellActions = jest.fn() as jest.MockedFunction<
  (props: { actions: unknown[]; item: unknown }) => void
>;

jest.mock("@swo/design-system/grid", () => ({
  GridCellActions: (props: { actions: unknown[]; item: unknown }) => {
    mockGridCellActions(props);
    return <div data-testid="grid-cell-actions" />;
  },
}));

jest.mock("@swo/design-system/utils", () => ({
  NO_VALUE: "—",
}));

describe("GridCellDynamicActions", () => {
  it("renders GridCellActions when actions exist", () => {
    const item = { id: "row-1" };
    const actions = [{ value: "edit", label: "Edit" }];

    render(<GridCellDynamicActions item={item} actions={actions} />);

    expect(screen.getByTestId("grid-cell-actions")).toBeInTheDocument();
    expect(mockGridCellActions).toHaveBeenCalledWith({ actions, item });
  });

  it("renders the NO_VALUE fallback when there are no actions", () => {
    render(<GridCellDynamicActions item={{ id: "row-1" }} actions={[]} />);

    expect(screen.getByText("—")).toBeInTheDocument();
    expect(mockGridCellActions).not.toHaveBeenCalled();
  });
});
