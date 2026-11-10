import type { ComponentProps } from "react";

import { render } from "@testing-library/react";

import { Status } from "./EntityStatusChip";

type MockStatusChipProps = ComponentProps<typeof import("@swo/mp-status-chip").StatusChip>;

const mockStatusChip = jest.fn() as jest.MockedFunction<(props: MockStatusChipProps) => void>;

jest.mock("@swo/mp-status-chip", () => ({
  StatusChip: ({ status }: MockStatusChipProps) => {
    mockStatusChip({ status });
    return <span data-testid="status-chip">{status}</span>;
  },
}));

describe("EntityStatusChip", () => {
  it.each([
    ["active", "Active"],
    ["Active", "Active"],
    ["", ""],
    ["dELETED", "DELETED"],
  ] as const)("renders status '%s' as '%s' in the StatusChip", (status, expected) => {
    render(<Status status={status} />);

    expect(mockStatusChip).toHaveBeenCalledWith({ status: expected });
  });
});
