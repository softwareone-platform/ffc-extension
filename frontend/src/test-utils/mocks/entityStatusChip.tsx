import type { ComponentProps } from "react";

import type { Status } from "~shared/components/entity-status-chip/EntityStatusChip";

type MockStatusProps = ComponentProps<typeof Status>;

export const mockStatus = jest.fn() as jest.MockedFunction<(props: MockStatusProps) => void>;

// Works for both `~shared/components/entity-status-chip` (barrel) and
// `~shared/components/entity-status-chip/EntityStatusChip` — mock whichever path the source imports.
export const mockEntityStatusChip = {
  Status: (props: MockStatusProps) => {
    mockStatus(props);
    return <span data-testid="status">{props.status}</span>;
  },
};
