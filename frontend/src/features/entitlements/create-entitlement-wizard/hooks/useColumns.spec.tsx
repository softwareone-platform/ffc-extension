import { render, renderHook, screen } from "@testing-library/react";

import { makeAccount } from "~test-utils";
import { mockCustomIcon } from "~test-utils/mocks/sharedGridCells";

import { useColumns } from "./useColumns";

jest.mock("~shared/components/custom-icons/CustomIcon", () => mockCustomIcon);

jest.mock("@swo/design-system/entity-reference", () => ({
  EntityReference: ({
    primaryContent,
    secondaryContent,
    icon,
  }: {
    primaryContent: React.ReactNode;
    secondaryContent: React.ReactNode;
    icon?: React.ReactNode;
  }) => (
    <div data-testid="entity-reference">
      <span data-testid="entity-primary">{primaryContent}</span>
      <span data-testid="entity-secondary">{secondaryContent}</span>
      <span data-testid="entity-icon">{icon}</span>
    </div>
  ),
}));

describe("useColumns (wizard)", () => {
  it("returns id (hidden) and name columns", () => {
    const { result } = renderHook(() => useColumns());

    expect(result.current.map((c) => c.name)).toEqual(["id", "name"]);
    expect(result.current[0].hide).toBe(true);
  });

  it("both columns are filterable", () => {
    const { result } = renderHook(() => useColumns());

    for (const col of result.current) {
      expect(col.filterable).toBe(true);
    }
  });

  it("renders the name column with an EntityReference showing name, id, and integration icon", () => {
    const { result } = renderHook(() => useColumns());
    const nameColumn = result.current.find((c) => c.name === "name")!;
    const item = { data: makeAccount({ id: "acc-1", name: "Acc", integration: "microsoft" }) };

    render(<>{(nameColumn.cell as (arg: { data: unknown }) => React.ReactNode)(item)}</>);

    expect(screen.getByTestId("entity-primary")).toHaveTextContent("Acc");
    expect(screen.getByTestId("entity-secondary")).toHaveTextContent("acc-1");
    expect(screen.getByTestId("custom-icon")).toHaveTextContent("microsoft");
  });

  it("falls back to 'unknown' icon when integration is missing", () => {
    const { result } = renderHook(() => useColumns());
    const nameColumn = result.current.find((c) => c.name === "name")!;
    const item = { data: makeAccount({ integration: null }) };

    render(<>{(nameColumn.cell as (arg: { data: unknown }) => React.ReactNode)(item)}</>);

    expect(screen.getByTestId("custom-icon")).toHaveTextContent("unknown");
  });
});
