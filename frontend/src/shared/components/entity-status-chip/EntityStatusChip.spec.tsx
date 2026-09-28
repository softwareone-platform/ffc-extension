import { render } from "@testing-library/react";

import { Status } from "./EntityStatusChip";

const mockStatusChip = jest.fn() as jest.MockedFunction<(props: { status: string }) => void>;

jest.mock("@swo/mp-status-chip", () => ({
  StatusChip: ({ status }: { status: string }) => {
    mockStatusChip({ status });
    return <span data-testid="status-chip">{status}</span>;
  },
}));

describe("EntityStatusChip", () => {
  beforeEach(() => {
    mockStatusChip.mockReset();
  });

  it.each([
    ["active", "Active"],
    ["Active", "Active"],
    ["", ""],
    ["dELETED", "DELETED"],
  ] as const)("passes %s as %s to StatusChip", (status, expected) => {
    render(<Status item={{ status }} />);

    expect(mockStatusChip).toHaveBeenCalledWith({ status: expected });
  });
});
